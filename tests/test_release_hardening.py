"""Static release guardrails for learner-controlled content and local data."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _relative_luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def _contrast_ratio(first: str, second: str) -> float:
    light, dark = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_learner_content_is_not_written_through_html_string_sinks() -> None:
    scripts = (
        "app.js",
        "voice.js",
        "learning.js",
        "memory.js",
        "career.js",
        "progress.js",
        "intelligence.js",
    )
    forbidden = re.compile(
        r"\.(?:innerHTML|outerHTML)\s*(?:=|\+=)|"
        r"\binsertAdjacentHTML\s*\(|\bdocument\.write\s*\("
    )
    for filename in scripts:
        source = (ROOT / "static" / filename).read_text(encoding="utf-8")
        assert not forbidden.search(source), f"Unsafe HTML string sink found in {filename}"


def test_local_secrets_databases_backups_and_models_are_git_ignored() -> None:
    ignored = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
    required = {".env", ".env.*", "data/", "prepped-backup-*.json", "*.sqlite", "*.sqlite3", "*.db", "models/", "*.onnx"}
    assert required <= ignored


def test_core_dark_theme_text_tokens_meet_wcag_aa_contrast_against_panel() -> None:
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    root = css.split("}", 1)[0]
    tokens = dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", root))
    panel = tokens["panel"]
    for token in ("text", "muted", "accent", "danger"):
        ratio = _contrast_ratio(tokens[token], panel)
        assert ratio >= 4.5, f"--{token} contrast is {ratio:.2f}:1"


def test_loopback_host_is_not_enough_when_peer_is_remote(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from prepped.main import create_app

    client = TestClient(
        create_app(db_path=tmp_path / "remote-peer.sqlite3"),
        client=("192.0.2.10", 43123),
    )
    with client:
        response = client.get("/api/health", headers={"Host": "127.0.0.1"})
    assert response.status_code == 400
    assert "local connections only" in response.text


def test_general_api_request_body_limit_is_enforced_before_json_parsing(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from prepped.main import create_app

    with TestClient(create_app(db_path=tmp_path / "body-limit.sqlite3")) as client:
        response = client.put(
            "/api/profile",
            content=b"x" * (1024 * 1024 + 1),
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 413


def test_request_size_middleware_rejects_invalid_content_length(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from prepped.main import create_app

    with TestClient(create_app(db_path=tmp_path / "bad-length.sqlite3")) as client:
        response = client.post(
            "/api/profile",
            content=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "not-a-number"},
        )
    assert response.status_code == 400


def test_chunked_api_body_limit_is_enforced_without_content_length() -> None:
    import asyncio
    from prepped.security import RequestSizeLimitMiddleware

    messages = iter((
        {"type": "http.request", "body": b"a" * 700_000, "more_body": True},
        {"type": "http.request", "body": b"b" * 400_000, "more_body": False},
    ))
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    async def app(scope, receive, send):
        await receive()
        await receive()

    middleware = RequestSizeLimitMiddleware(app)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/profile",
        "headers": [],
    }
    asyncio.run(middleware(scope, receive, send))
    assert sent[0]["status"] == 413

def test_checkout_html_and_static_assets_revalidate_after_local_updates(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from prepped.main import create_app

    with TestClient(create_app(db_path=tmp_path / "cache-headers.sqlite3")) as client:
        html = client.get("/")
        script = client.get("/static/app.js")
        api = client.get("/api/health")

    assert html.headers.get("cache-control") == "no-cache"
    assert script.headers.get("cache-control") == "no-cache"
    assert api.headers.get("cache-control") == "no-store"

