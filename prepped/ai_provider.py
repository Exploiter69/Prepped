"""Optional, provider-neutral cloud AI adapter with explicit consent and free-tier awareness (Pack D).

Security and privacy guarantees:
- Prepped works 100% locally without any cloud AI provider configured.
- API keys are never returned to frontend JS, never exported in backups, and never logged.
- Every cloud request requires explicit `consent_confirmed=True` from the learner.
- Raw audio recordings are never sent by this module.
- Never silently switches to another provider or promises permanent free-tier availability.
"""
from __future__ import annotations

import json
import logging
import os
import stat
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prepped.database import connect_database

logger = logging.getLogger(__name__)

ProviderName = Literal["none", "gemini", "groq"]
AssistTask = Literal["transcript_feedback", "project_feedback", "interview_feedback", "generate_questions"]

DEFAULT_MODELS: dict[str, str] = {
    "gemini": os.environ.get("PREPPED_GEMINI_MODEL", "gemini-2.5-flash"),
    "groq": os.environ.get("PREPPED_GROQ_MODEL", "llama-3.3-70b-versatile"),
}

MAX_INPUT_CHARS = 6_000
REQUEST_TIMEOUT_SECONDS = 25.0

AI_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS ai_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
    provider TEXT NOT NULL DEFAULT 'none' CHECK (provider IN ('none', 'gemini', 'groq')),
    model TEXT NOT NULL DEFAULT '',
    consent_acknowledged INTEGER NOT NULL DEFAULT 0 CHECK (consent_acknowledged IN (0, 1)),
    daily_request_limit INTEGER NOT NULL DEFAULT 25 CHECK (daily_request_limit BETWEEN 1 AND 200),
    requests_today INTEGER NOT NULL DEFAULT 0 CHECK (requests_today >= 0),
    requests_date TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
"""


class AIProviderError(Exception):
    def __init__(self, status_code: int, public_message: str, code: str = "provider_error") -> None:
        super().__init__(public_message)
        self.status_code = status_code
        self.public_message = public_message
        self.code = code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today_iso() -> str:
    return date.today().isoformat()


def _credentials_path(db_path: Path) -> Path:
    return Path(db_path).parent / ".ai_keys.json"


def _read_local_keys(db_path: Path) -> dict[str, str]:
    path = _credentials_path(db_path)
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {k: str(v).strip() for k, v in raw.items() if k in {"gemini", "groq"} and isinstance(v, str) and v.strip()}
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def _write_local_key(db_path: Path, provider: str, api_key: str) -> None:
    if provider not in {"gemini", "groq"}:
        raise ValueError("Unsupported provider.")
    path = _credentials_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise OSError("Refusing to write credentials through a symlink.")
    keys = _read_local_keys(db_path)
    cleaned = api_key.strip()
    if cleaned:
        keys[provider] = cleaned
    else:
        keys.pop(provider, None)
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    try:
        os.write(fd, json.dumps(keys, indent=2).encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def resolve_api_key(db_path: Path, provider: str) -> tuple[str | None, str]:
    env_map = {"gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY"}
    env_var = env_map.get(provider)
    if env_var:
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            return env_val, "environment"
    local_keys = _read_local_keys(db_path)
    if local_keys.get(provider):
        return local_keys[provider], "local_file"
    return None, "none"


def initialize_ai_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as conn:
        conn.executescript(AI_SETTINGS_TABLE)


def load_ai_settings(db_path: Path) -> dict[str, Any]:
    today = _today_iso()
    with connect_database(Path(db_path)) as conn:
        row = conn.execute("SELECT * FROM ai_settings WHERE id = 1").fetchone()
    if row is None:
        settings = {
            "enabled": False,
            "provider": "none",
            "model": "",
            "consent_acknowledged": False,
            "daily_request_limit": 25,
            "requests_today": 0,
            "requests_date": today,
            "updated_at": None,
        }
    else:
        req_today = int(row["requests_today"]) if row["requests_date"] == today else 0
        settings = {
            "enabled": bool(row["enabled"]),
            "provider": row["provider"],
            "model": row["model"] or DEFAULT_MODELS.get(row["provider"], ""),
            "consent_acknowledged": bool(row["consent_acknowledged"]),
            "daily_request_limit": int(row["daily_request_limit"]),
            "requests_today": req_today,
            "requests_date": today,
            "updated_at": row["updated_at"],
        }
    active_provider = settings["provider"]
    key_val, key_source = resolve_api_key(db_path, active_provider) if active_provider in {"gemini", "groq"} else (None, "none")
    gemini_key, gemini_src = resolve_api_key(db_path, "gemini")
    groq_key, groq_src = resolve_api_key(db_path, "groq")
    return {
        **settings,
        "has_api_key": bool(key_val),
        "key_source": key_source,
        "providers": {
            "gemini": {"default_model": DEFAULT_MODELS["gemini"], "has_key": bool(gemini_key), "key_source": gemini_src},
            "groq": {"default_model": DEFAULT_MODELS["groq"], "has_key": bool(groq_key), "key_source": groq_src},
        },
        "privacy_notice": (
            "Cloud AI is strictly optional. Requests send only the text you review and confirm to your chosen provider. "
            "Raw audio recordings are never sent. Free-tier quotas and availability can change at any time; local practice always works offline."
        ),
    }


def _http_post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float = REQUEST_TIMEOUT_SECONDS) -> tuple[int, dict[str, Any]]:
    try:
        import httpx  # type: ignore

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            try:
                data = resp.json()
            except Exception:
                data = {}
            return resp.status_code, data if isinstance(data, dict) else {}
    except ImportError:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {}
            return exc.code, parsed if isinstance(parsed, dict) else {}


def _map_provider_http_error(provider: str, status_code: int) -> AIProviderError:
    label = "Google Gemini" if provider == "gemini" else "Groq"
    if status_code in (401, 403):
        return AIProviderError(
            401,
            f"{label} rejected the configured API key. Check your key in Profile -> Cloud AI or continue with offline feedback.",
            "invalid_key",
        )
    if status_code == 429:
        return AIProviderError(
            429,
            f"{label} rate limit or free-tier quota was reached. Local deterministic feedback remains available offline.",
            "quota_exceeded",
        )
    if status_code == 404:
        return AIProviderError(
            400,
            f"The configured {label} model was not found or is no longer supported. Update the model name in Cloud AI settings.",
            "unsupported_model",
        )
    if status_code >= 500:
        return AIProviderError(
            502,
            f"{label} is temporarily unavailable (HTTP {status_code}). Local offline features continue working normally.",
            "provider_outage",
        )
    return AIProviderError(
        502,
        f"{label} could not process this request (HTTP {status_code}). You can continue offline.",
        "provider_error",
    )


def call_cloud_provider(
    provider: str,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    *,
    http_post=_http_post_json,
) -> str:
    chosen_model = (model or DEFAULT_MODELS.get(provider, "")).strip()
    if not chosen_model:
        raise AIProviderError(400, "Choose a model name before sending a cloud AI request.", "missing_model")
    if not api_key:
        raise AIProviderError(400, "No API key is configured for the selected provider.", "missing_key")

    if provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.35, "maxOutputTokens": 700},
        }
    elif provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "model": chosen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.35,
            "max_tokens": 700,
        }
    else:
        raise AIProviderError(400, "Cloud AI provider is disabled.", "disabled")

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            status_code, data = http_post(url, headers, payload, REQUEST_TIMEOUT_SECONDS)
        except TimeoutError as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(0.3)
                continue
            raise AIProviderError(504, "The cloud AI request timed out. Local offline feedback remains available.", "timeout") from exc
        except Exception as exc:
            last_exc = exc
            logger.warning("Cloud AI network error for provider=%s (%s)", provider, type(exc).__name__)
            raise AIProviderError(503, "Could not reach the cloud AI provider. Check your connection or continue offline.", "network_error") from exc

        if status_code in (502, 503) and attempt == 0:
            time.sleep(0.4)
            continue
        if status_code >= 400:
            raise _map_provider_http_error(provider, status_code)

        text = ""
        if provider == "gemini":
            candidates = data.get("candidates") or []
            if candidates and isinstance(candidates[0], dict):
                parts = (candidates[0].get("content") or {}).get("parts") or []
                text = "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()
        else:
            choices = data.get("choices") or []
            if choices and isinstance(choices[0], dict):
                text = str((choices[0].get("message") or {}).get("content", "")).strip()
        if not text:
            raise AIProviderError(502, "The cloud AI provider returned an empty response. Try again or use local feedback.", "empty_response")
        return text

    raise AIProviderError(503, "Cloud AI is currently unavailable. Continue with offline practice.", "network_error") from last_exc


def _build_task_prompts(task: AssistTask, content: str, context: str) -> tuple[str, str]:
    system = (
        "You are a calm, encouraging English and engineering placement coach for college students. "
        "Be concrete, brief, and honest. Never assign CEFR levels, numeric scores, or placement predictions. "
        "Structure your response cleanly with short bullet points: Strengths, What to clarify (max 3), and One clearer rewrite."
    )
    if task == "transcript_feedback":
        user = f"Prompt context: {context or 'Project explanation'}\n\nLearner transcript:\n{content}\n\nGive specific grammar/clarity feedback and one clearer spoken rewrite."
    elif task == "project_feedback":
        user = f"Project notes ({context or 'Student project'}):\n{content}\n\nReview clarity of Problem, Role, Trade-offs, and Outcome, and suggest 2 likely interviewer follow-up questions."
    elif task == "interview_feedback":
        user = f"Interview question: {context or 'General placement question'}\n\nLearner answer:\n{content}\n\nGive concise coaching on clarity and one realistic follow-up question."
    else:
        user = f"Learner background / project material:\n{content}\n\nGenerate 5 practical, respectful interview questions tailored strictly to this material (numbered 1 to 5)."
    return system, user


class AIConfigUpdate(BaseModel):
    enabled: bool = False
    provider: ProviderName = "none"
    model: str = Field(default="", max_length=120)
    consent_acknowledged: bool = False
    daily_request_limit: int = Field(default=25, ge=1, le=200)


class AIKeyUpdate(BaseModel):
    provider: Literal["gemini", "groq"]
    api_key: str = Field(default="", max_length=300)


class AIAssistRequest(BaseModel):
    task: AssistTask
    content: str = Field(min_length=5, max_length=MAX_INPUT_CHARS)
    context: str = Field(default="", max_length=600)
    consent_confirmed: bool = False


def create_ai_router(db_path: Path, *, http_post=_http_post_json) -> APIRouter:
    router = APIRouter(prefix="/api/ai", tags=["ai"])

    @router.get("/config")
    def get_ai_config() -> dict[str, Any]:
        return {"ai": load_ai_settings(Path(db_path))}

    @router.put("/config")
    def update_ai_config(payload: AIConfigUpdate) -> dict[str, Any]:
        now = _now()
        today = _today_iso()
        model = payload.model.strip() or DEFAULT_MODELS.get(payload.provider, "")
        with connect_database(Path(db_path)) as conn:
            existing = conn.execute("SELECT requests_today, requests_date FROM ai_settings WHERE id = 1").fetchone()
            req_today = int(existing["requests_today"]) if (existing and existing["requests_date"] == today) else 0
            conn.execute(
                """
                INSERT INTO ai_settings
                    (id, enabled, provider, model, consent_acknowledged, daily_request_limit,
                     requests_today, requests_date, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    provider = excluded.provider,
                    model = excluded.model,
                    consent_acknowledged = excluded.consent_acknowledged,
                    daily_request_limit = excluded.daily_request_limit,
                    updated_at = excluded.updated_at
                """,
                (
                    int(payload.enabled), payload.provider, model,
                    int(payload.consent_acknowledged), payload.daily_request_limit,
                    req_today, today, now,
                ),
            )
        return {"ai": load_ai_settings(Path(db_path))}

    @router.post("/key")
    def save_ai_key(payload: AIKeyUpdate) -> dict[str, Any]:
        _write_local_key(Path(db_path), payload.provider, payload.api_key)
        return {
            "saved": bool(payload.api_key.strip()),
            "provider": payload.provider,
            "ai": load_ai_settings(Path(db_path)),
        }

    @router.post("/test")
    def test_ai_connection() -> dict[str, Any]:
        cfg = load_ai_settings(Path(db_path))
        if cfg["provider"] not in {"gemini", "groq"}:
            raise HTTPException(status_code=400, detail="Select Gemini or Groq before testing the connection.")
        api_key, _ = resolve_api_key(Path(db_path), cfg["provider"])
        if not api_key:
            raise HTTPException(status_code=400, detail="Configure an API key (via environment variable or local key field) first.")
        try:
            reply = call_cloud_provider(
                cfg["provider"],
                cfg["model"],
                api_key,
                "Reply with exactly: Connection verified.",
                "Ping.",
                http_post=http_post,
            )
        except AIProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
        return {"ok": True, "provider": cfg["provider"], "model": cfg["model"], "preview": reply[:120]}

    @router.post("/assist")
    def request_ai_assist(payload: AIAssistRequest) -> dict[str, Any]:
        if payload.consent_confirmed is not True:
            raise HTTPException(
                status_code=400,
                detail="Explicit consent is required before sending learner text to a cloud AI provider.",
            )
        cfg = load_ai_settings(Path(db_path))
        if not cfg["enabled"] or cfg["provider"] not in {"gemini", "groq"}:
            raise HTTPException(
                status_code=400,
                detail="Optional cloud AI is currently off. Enable it in Profile -> Cloud AI or continue with offline feedback.",
            )
        if cfg["requests_today"] >= cfg["daily_request_limit"]:
            raise HTTPException(
                status_code=429,
                detail=f"You reached your local daily cloud AI cap ({cfg['daily_request_limit']} requests). Local offline practice remains fully available.",
            )
        api_key, _ = resolve_api_key(Path(db_path), cfg["provider"])
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="No API key is configured for the selected cloud AI provider. Add a key or continue offline.",
            )
        system_prompt, user_prompt = _build_task_prompts(payload.task, payload.content.strip(), payload.context.strip())
        try:
            response_text = call_cloud_provider(
                cfg["provider"], cfg["model"], api_key, system_prompt, user_prompt, http_post=http_post
            )
        except AIProviderError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc

        today = _today_iso()
        with connect_database(Path(db_path)) as conn:
            conn.execute(
                "UPDATE ai_settings SET requests_today = CASE WHEN requests_date = ? THEN requests_today + 1 ELSE 1 END, requests_date = ?, updated_at = ? WHERE id = 1",
                (today, today, _now()),
            )
        updated = load_ai_settings(Path(db_path))
        return {
            "provider": cfg["provider"],
            "model": cfg["model"],
            "task": payload.task,
            "response": response_text,
            "requests_today": updated["requests_today"],
            "daily_request_limit": updated["daily_request_limit"],
            "note": "Generated by your configured cloud AI provider after explicit consent. Review critically; this is not a graded assessment.",
        }

    return router
