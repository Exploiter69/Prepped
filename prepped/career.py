"""Local, data-driven career interview studios with transparent formative review."""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STUDIOS_PATH = ROOT / "content" / "career-studios.v1.json"
STUDIO_IDS = {"project-explanation", "hr-behavioural", "technical-fundamentals"}
MAX_QUESTIONS = 8
CONTEXTUAL_TRIGGERS = {
    "no_example_marker": (
        re.compile(r"\b(for example|for instance|such as|e\.g\.|when I|when we|in my project)\b", re.I),
        "a concrete example",
    ),
    "no_first_person_action": (
        re.compile(r"\b(I built|I designed|I implemented|I tested|I led|I coordinated|my role|I was responsible)\b", re.I),
        "your personal action",
    ),
    "no_reasoning_marker": (
        re.compile(r"\b(because|so that|therefore|as a result|which meant|the reason|trade[- ]off)\b", re.I),
        "your reasoning or trade-off",
    ),
    "no_evidence_marker": (
        re.compile(r"\b(tested|test|measured|measurement|observed|evidence|result|output|logs|feedback|verified)\b", re.I),
        "a test, observation, or result",
    ),
    "no_sequence_marker": (
        re.compile(r"\b(first|next|then|after|finally|request|response|route|handler)\b", re.I),
        "the sequence of steps",
    ),
    "no_reflection_marker": (
        re.compile(r"\b(learned|learnt|next time|in future|improve|change|would do differently)\b", re.I),
        "a lesson or reflection",
    ),
    "no_preparation_marker": (
        re.compile(r"\b(researched|read about|practised|practiced|built|explored|studied|learned|learnt)\b", re.I),
        "a preparation step",
    ),
    "no_tradeoff_marker": (
        re.compile(r"\b(trade[- ]off|downside|drawback|cost|whereas|however|limitation)\b", re.I),
        "a trade-off or limitation",
    ),
}


def _contextual_followup(question: dict[str, Any], answer: str, difficulty: str) -> dict[str, Any]:
    """Select an authored follow-up from a narrow, explainable text cue."""
    contextual = question.get("contextual_followup")
    if isinstance(contextual, dict):
        trigger = contextual.get("trigger")
        rule = CONTEXTUAL_TRIGGERS.get(trigger)
        prompt = contextual.get("prompt")
        if rule and isinstance(prompt, str) and prompt.strip() and not rule[0].search(answer):
            return {
                "question_id": question["id"],
                "turn_type": "followup",
                "prompt": prompt,
                "simpler_prompt": contextual.get("simpler_prompt", prompt),
                "clarification": contextual.get("clarification", ""),
                "context_note": (
                    f"This follow-up invites {rule[1]}. A simple text cue was not detected; "
                    "the heuristic may miss equivalent wording. It is not an assessment of your answer."
                ),
            }
    authored = question["followup"]
    variants = authored.get("prompts", {})
    return {
        "question_id": question["id"],
        "turn_type": "followup",
        "prompt": variants.get(difficulty, authored["prompt"]),
        "simpler_prompt": authored.get("simpler_prompt", variants.get(difficulty, authored["prompt"])),
        "clarification": authored.get("clarification", ""),
        "context_note": "This follow-up follows your selected practice level; it is not a judgement of correctness.",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_studios(path: Path = DEFAULT_STUDIOS_PATH) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Career studio content is missing or invalid.") from exc
    if not isinstance(data, dict) or data.get("version") != "1.3.0" or not isinstance(data.get("studios"), list):
        raise ValueError("Career studio catalog must contain version 1.3.0 and a studios list.")
    review = data.get("review")
    if (not isinstance(review, dict) or review.get("status") != "ai_assisted_editorial_review"
            or not review.get("reviewer") or not review.get("reviewed_on")
            or review.get("human_review_required") is not True):
        raise ValueError("Career catalog review record must disclose AI-assisted review and pending human sign-off.")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Career catalog must include a source register.")
    source_index = {}
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get("id"), str)
                or source["id"] in source_index or not source.get("title") or not source.get("publisher")
                or not isinstance(source.get("url"), str) or not source["url"].startswith("https://")
                or not source.get("checked_on") or not source.get("supports")):
            raise ValueError("Career source register contains incomplete or duplicate entries.")
        source_index[source["id"]] = source
    seen: set[str] = set()
    for studio in data["studios"]:
        if not isinstance(studio, dict) or studio.get("id") not in STUDIO_IDS:
            raise ValueError("Career studio has an unknown or missing id.")
        if studio["id"] in seen:
            raise ValueError("Career studio ids must be unique.")
        seen.add(studio["id"])
        if (not studio.get("title") or not studio.get("description")
                or not isinstance(studio.get("estimated_minutes"), int) or studio["estimated_minutes"] < 1
                or not isinstance(studio.get("learning_outcomes"), list) or not studio["learning_outcomes"]
                or not isinstance(studio.get("skill_ids"), list) or not studio["skill_ids"]
                or not isinstance(studio.get("source_ids", []), list)
                or any(source_id not in source_index for source_id in studio.get("source_ids", []))):
            raise ValueError("Career studio needs outcomes, skill mappings, and valid source references.")
        content_review = studio.get("content_review")
        if (not isinstance(content_review, dict) or content_review.get("status") != "ai_assisted_editorial_review"
                or not content_review.get("reviewer") or not content_review.get("reviewed_on")
                or content_review.get("human_review_required") is not True):
            raise ValueError("Career studio needs a transparent review record and human sign-off flag.")
        questions = studio.get("questions")
        if not isinstance(questions, list) or not questions or len(questions) > MAX_QUESTIONS:
            raise ValueError("Each studio must contain between 1 and 8 primary questions.")
        qids: set[str] = set()
        for question in questions:
            if not isinstance(question, dict) or not isinstance(question.get("id"), str) or not question.get("prompt"):
                raise ValueError("Every career question needs an id and prompt.")
            if question["id"] in qids:
                raise ValueError("Career question ids must be unique within a studio.")
            if (not isinstance(question.get("learning_outcome"), str) or not question["learning_outcome"].strip()
                    or not isinstance(question.get("skill_ids"), list) or not question["skill_ids"]
                    or any(skill_id not in studio["skill_ids"] for skill_id in question["skill_ids"])):
                raise ValueError("Every career question needs an observable outcome and a valid studio skill mapping.")
            qids.add(question["id"])
            followup = question.get("followup")
            if not isinstance(followup, dict) or not isinstance(followup.get("prompt"), str):
                raise ValueError("Every primary question needs one authored follow-up.")
            contextual = question.get("contextual_followup")
            if contextual is not None:
                if (
                    not isinstance(contextual, dict)
                    or not isinstance(contextual.get("trigger"), str)
                    or contextual.get("trigger") not in CONTEXTUAL_TRIGGERS
                    or not isinstance(contextual.get("prompt"), str)
                    or not contextual["prompt"].strip()
                ):
                    raise ValueError("A contextual follow-up needs a supported trigger and non-empty authored prompt.")
            for prompt_group in (question, followup, contextual or {}):
                for optional_text in ("simpler_prompt", "clarification"):
                    if optional_text in prompt_group and (
                        not isinstance(prompt_group[optional_text], str) or not prompt_group[optional_text].strip()
                    ):
                        raise ValueError("Simpler prompts and clarification text must be non-empty strings.")
    if seen != STUDIO_IDS:
        raise ValueError("The career catalog must include all three studios.")
    return data


def initialize_career_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS career_sessions (
            id TEXT PRIMARY KEY,
            studio_id TEXT NOT NULL,
            studio_version TEXT NOT NULL,
            studio_json TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK (difficulty IN ('guided','standard','challenging')),
            status TEXT NOT NULL CHECK (status IN ('in_progress','completed','cancelled')),
            current_question_index INTEGER NOT NULL DEFAULT 0,
            pending_followup_json TEXT,
            attempt_group_id TEXT NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS career_turns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES career_sessions(id) ON DELETE CASCADE,
            turn_index INTEGER NOT NULL,
            question_id TEXT NOT NULL,
            turn_type TEXT NOT NULL CHECK (turn_type IN ('primary','followup')),
            prompt TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(session_id, turn_index)
        );
        CREATE INDEX IF NOT EXISTS idx_career_sessions_created ON career_sessions(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_career_turns_session ON career_turns(session_id, turn_index);
        """)


class StartInterview(BaseModel):
    studio_id: str
    difficulty: Literal["guided", "standard", "challenging"] = "standard"

    @field_validator("studio_id")
    @classmethod
    def valid_studio(cls, value: str) -> str:
        if value not in STUDIO_IDS:
            raise ValueError("Choose an available interview studio.")
        return value


class SubmitInterviewAnswer(BaseModel):
    answer_text: str = Field(min_length=1, max_length=6000)
    prompt_variant: Literal["original", "simplified"] = "original"

    @field_validator("answer_text")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Write or transcribe an answer before continuing.")
        return value


def _session(connection: sqlite3.Connection, session_id: str) -> sqlite3.Row:
    row = connection.execute("SELECT * FROM career_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return row


def _turns(connection: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(
        "SELECT * FROM career_turns WHERE session_id = ? ORDER BY turn_index", (session_id,)
    ).fetchall()]


def _current_prompt(row: sqlite3.Row) -> dict[str, Any] | None:
    if row["status"] != "in_progress":
        return None
    if row["pending_followup_json"]:
        return json.loads(row["pending_followup_json"])
    studio = json.loads(row["studio_json"])
    index = row["current_question_index"]
    if index >= len(studio["questions"]):
        return None
    question = studio["questions"][index]
    return {
        "question_id": question["id"], "turn_type": "primary", "prompt": question["prompt"],
        "simpler_prompt": question.get("simpler_prompt", question["prompt"]),
        "clarification": question.get("clarification", ""),
    }


def _session_view(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    turns = _turns(connection, row["id"])
    studio = json.loads(row["studio_json"])
    return {
        "id": row["id"], "studio_id": row["studio_id"], "studio_title": studio["title"],
        "studio_version": row["studio_version"], "difficulty": row["difficulty"],
        "status": row["status"], "created_at": row["created_at"], "completed_at": row["completed_at"],
        "attempt_group_id": row["attempt_group_id"], "attempt_number": row["attempt_number"],
        "primary_question_count": len(studio["questions"]), "turn_count": len(turns),
        "answered_primary_count": len({t["question_id"] for t in turns if t["turn_type"] == "primary"}),
        "current_prompt": _current_prompt(row),
        "turns": turns,
    }


def _feedback(
    studio: dict[str, Any],
    turns: list[dict[str, Any]],
    previous_turns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    notes = []
    for turn in turns:
        answer = turn["answer_text"]
        words = re.findall(r"\b[\w'-]+\b", answer)
        checks = []
        checks.append({
            "criterion": "Developed response",
            "observed": len(words) >= 25,
            "evidence": f"{len(words)} words" if words else "No words detected",
            "guidance": "Add enough detail to explain the idea; there is no required word count." if len(words) < 25 else "The response contains enough material to review in context.",
        })
        example = re.search(r"\b(for example|for instance|such as|e\.g\.|when I|when we|in my project)\b", answer, re.I)
        checks.append({
            "criterion": "Concrete example",
            "observed": bool(example),
            "evidence": answer[max(0, example.start()-45):min(len(answer), example.end()+100)] if example else None,
            "guidance": "Consider adding a specific example, action, or situation." if not example else "A concrete example marker appears; check that the example is accurate and relevant.",
        })
        reason = re.search(r"\b(because|so that|therefore|as a result|which meant|the reason|trade[- ]off)\b", answer, re.I)
        checks.append({
            "criterion": "Reasoning or outcome",
            "observed": bool(reason),
            "evidence": answer[max(0, reason.start()-45):min(len(answer), reason.end()+100)] if reason else None,
            "guidance": "Explain why you made the choice or what happened as a result." if not reason else "A reasoning or outcome phrase appears; make sure it connects to the question.",
        })
        evidence = re.search(r"\b(tested|test|measured|measurement|observed|evidence|result|output|logs|feedback|verified)\b", answer, re.I)
        checks.append({
            "criterion": "Evidence or outcome",
            "observed": bool(evidence),
            "evidence": answer[max(0, evidence.start()-45):min(len(answer), evidence.end()+100)] if evidence else None,
            "guidance": "Name a test, observation, or result and explain what it does and does not show." if not evidence else "An evidence-related cue appears; make its connection to the claim explicit.",
        })
        if not example:
            coaching = {
                "action": "Add one specific example: describe the situation, what you did, and what happened.",
                "basis": "A common example cue was not detected in this answer. Equivalent wording may have been missed.",
                "evidence": None,
            }
        elif not reason:
            coaching = {
                "action": "Connect your action to a reason or outcome: explain why you chose it or what changed.",
                "basis": "A common reasoning cue was not detected in this answer. This does not mean the reasoning is absent.",
                "evidence": answer[max(0, example.start()-45):min(len(answer), example.end()+100)],
            }
        elif not evidence:
            coaching = {
                "action": "Make one claim easier to verify by naming a test, observation, or concrete result.",
                "basis": "A common evidence cue was not detected in this answer. The heuristic may miss equivalent wording.",
                "evidence": answer[max(0, reason.start()-45):min(len(answer), reason.end()+100)],
            }
        else:
            coaching = {
                "action": "State what your evidence supports and one limitation it does not resolve.",
                "basis": "Example, reasoning, and evidence-related text cues were detected; their accuracy and relevance still need human judgement.",
                "evidence": answer[max(0, evidence.start()-45):min(len(answer), evidence.end()+100)],
            }
        notes.append({
            "question_id": turn["question_id"], "turn_type": turn["turn_type"],
            "prompt": turn["prompt"], "answer": answer, "checks": checks, "coaching": coaching,
        })
    comparisons = []
    if previous_turns:
        previous_by_key = {(turn["question_id"], turn["turn_type"]): turn for turn in previous_turns}
        for turn in turns:
            previous = previous_by_key.get((turn["question_id"], turn["turn_type"]))
            if previous:
                comparisons.append({
                    "question_id": turn["question_id"],
                    "turn_type": turn["turn_type"],
                    "previous_prompt": previous["prompt"],
                    "current_prompt": turn["prompt"],
                    "previous_answer": previous["answer_text"],
                    "current_answer": turn["answer_text"],
                })
    return {
        "title": "Interview review",
        "disclaimer": "These are transparent text-based reflection prompts, not an expert interview rating, technical correctness check, hiring decision, or placement prediction. Keyword signals can miss valid answers and can also match weak ones.",
        "notes": notes,
        "attempt_comparison": comparisons,
        "comparison_note": (
            "Compare your wording, examples, reasoning, and evidence for yourself. Differences between attempts are not a measured improvement."
            if comparisons else None
        ),
        "next_steps": [
            "Choose one answer and make its example more specific.",
            "Explain one decision and the reason behind it.",
            "Retry the studio and compare your own wording; there is no overall score.",
        ],
    }


def create_career_router(db_path: Path, studios_path: Path = DEFAULT_STUDIOS_PATH) -> APIRouter:
    router = APIRouter(prefix="/api/career", tags=["career"])

    @router.get("/studios")
    def list_studios() -> dict[str, Any]:
        try:
            catalog = load_studios(studios_path)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"version": catalog["version"], "studios": [
            {key: studio[key] for key in ("id", "title", "category", "description", "estimated_minutes", "question_count", "skills")}
            for studio in catalog["studios"]
        ]}

    @router.get("/studios/{studio_id}")
    def get_studio(studio_id: str) -> dict[str, Any]:
        try:
            catalog = load_studios(studios_path)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        studio = next((item for item in catalog["studios"] if item["id"] == studio_id), None)
        if studio is None:
            raise HTTPException(status_code=404, detail="Interview studio not found.")
        return {key: value for key, value in studio.items() if key != "questions"} | {
            "question_count": len(studio["questions"])
        }

    @router.post("/sessions", status_code=201)
    def start(payload: StartInterview) -> dict[str, Any]:
        try:
            catalog = load_studios(studios_path)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        studio = next((item for item in catalog["studios"] if item["id"] == payload.studio_id), None)
        if studio is None:
            raise HTTPException(status_code=404, detail="Interview studio not found.")
        session_id = str(uuid4())
        now = _now()
        with connect_database(Path(db_path)) as connection:
            connection.execute(
                """INSERT INTO career_sessions
                (id, studio_id, studio_version, studio_json, difficulty, status, attempt_group_id, created_at)
                VALUES (?, ?, ?, ?, ?, 'in_progress', ?, ?)""",
                (session_id, studio["id"], catalog["version"], json.dumps(studio, ensure_ascii=False),
                 payload.difficulty, session_id, now),
            )
            return _session_view(connection, _session(connection, session_id))

    @router.get("/sessions")
    def history() -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            rows = connection.execute(
                "SELECT * FROM career_sessions ORDER BY created_at DESC, rowid DESC LIMIT 100"
            ).fetchall()
            sessions = [_session_view(connection, row) for row in rows]
        return {"sessions": sessions, "count": len(sessions)}

    @router.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            return _session_view(connection, _session(connection, session_id))

    @router.post("/sessions/{session_id}/answers")
    def answer(session_id: str, payload: SubmitInterviewAnswer) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            row = _session(connection, session_id)
            if row["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="This interview is no longer accepting answers.")
            current = _current_prompt(row)
            if current is None:
                raise HTTPException(status_code=409, detail="There is no unanswered interview prompt.")
            turns = _turns(connection, session_id)
            connection.execute(
                """INSERT INTO career_turns
                (id, session_id, turn_index, question_id, turn_type, prompt, answer_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid4()), session_id, len(turns), current["question_id"], current["turn_type"],
                 (current.get("simpler_prompt") if payload.prompt_variant == "simplified" else None) or current["prompt"],
                 payload.answer_text, _now()),
            )
            studio = json.loads(row["studio_json"])
            pending = None
            question_index = row["current_question_index"]
            if current["turn_type"] == "primary":
                authored_question = studio["questions"][question_index]
                pending = _contextual_followup(authored_question, payload.answer_text, row["difficulty"])
            else:
                question_index += 1
            completed_at = None
            status = "in_progress"
            if question_index >= len(studio["questions"]) and pending is None:
                status, completed_at = "completed", _now()
            connection.execute(
                """UPDATE career_sessions SET current_question_index = ?, pending_followup_json = ?,
                status = ?, completed_at = ? WHERE id = ?""",
                (question_index, json.dumps(pending, ensure_ascii=False) if pending else None,
                 status, completed_at, session_id),
            )
            updated = _session(connection, session_id)
            result = _session_view(connection, updated)
            if status == "completed":
                result["feedback"] = _feedback(studio, result["turns"])
            return result

    @router.get("/sessions/{session_id}/feedback")
    def feedback(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            row = _session(connection, session_id)
            if row["status"] != "completed":
                raise HTTPException(status_code=409, detail="Complete the interview before reviewing feedback.")
            previous = connection.execute(
                """SELECT id FROM career_sessions
                WHERE attempt_group_id = ? AND attempt_number < ? AND status = 'completed'
                ORDER BY attempt_number DESC LIMIT 1""",
                (row["attempt_group_id"], row["attempt_number"]),
            ).fetchone()
            previous_turns = _turns(connection, previous["id"]) if previous else None
            return _feedback(json.loads(row["studio_json"]), _turns(connection, session_id), previous_turns)

    @router.post("/sessions/{session_id}/retry", status_code=201)
    def retry(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            previous = _session(connection, session_id)
            if previous["status"] != "completed":
                raise HTTPException(status_code=409, detail="Complete this interview before retrying.")
            next_attempt = connection.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) + 1 AS n FROM career_sessions WHERE attempt_group_id = ?",
                (previous["attempt_group_id"],),
            ).fetchone()["n"]
            new_id, now = str(uuid4()), _now()
            connection.execute(
                """INSERT INTO career_sessions
                (id, studio_id, studio_version, studio_json, difficulty, status, attempt_group_id, attempt_number, created_at)
                VALUES (?, ?, ?, ?, ?, 'in_progress', ?, ?, ?)""",
                (new_id, previous["studio_id"], previous["studio_version"], previous["studio_json"],
                 previous["difficulty"], previous["attempt_group_id"], next_attempt, now),
            )
            return _session_view(connection, _session(connection, new_id))

    @router.delete("/sessions/{session_id}", status_code=204)
    def delete(session_id: str) -> None:
        with connect_database(Path(db_path)) as connection:
            cursor = connection.execute("DELETE FROM career_sessions WHERE id = ?", (session_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Interview session not found.")
        return None

    return router
