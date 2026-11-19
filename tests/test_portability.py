from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app


def client_for(path: Path) -> TestClient:
    client = TestClient(create_app(db_path=path))
    client.__enter__()
    return client


def test_export_and_restore_round_trip_all_local_user_tables(tmp_path: Path) -> None:
    source = client_for(tmp_path / "source.sqlite3")
    target = client_for(tmp_path / "target.sqlite3")
    try:
        source.put("/api/profile", json={"display_name": "Source learner", "primary_goal": "english_fluency"})
        source.post("/api/sessions")
        source.post("/api/memory/items", json={
            "item_type": "phrase", "front": "Could you clarify?", "back": "A polite request for more detail.",
        })
        source.post("/api/goals", json={
            "title": "Complete lessons", "goal_type": "lessons_completed", "target_count": 2,
        })
        exported = source.get("/api/data/export")
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("application/json")
        backup = exported.json()
        assert backup["format"] == "prepped-local-backup"
        assert set(backup["tables"]) == {
            "learner_profile", "sessions", "answers", "learning_attempts", "learning_events",
            "learning_memory", "learning_memory_reviews", "career_sessions", "career_turns", "learner_goals",
        }
        assert backup["tables"]["sessions"]
        assert backup["tables"]["learning_memory"]
        assert backup["tables"]["learner_goals"]

        target.put("/api/profile", json={"display_name": "Target learner"})
        restore_payload = {**backup, "confirm_replace": True}
        restored = target.post("/api/data/restore", json=restore_payload)
        assert restored.status_code == 200, restored.text
        assert restored.json()["restored"] is True
        assert target.get("/api/profile").json()["profile"]["display_name"] == "Source learner"
        status = target.get("/api/data/status").json()
        assert status["counts"]["sessions"] == 1
        assert status["counts"]["learning_memory"] == 1
        assert status["counts"]["learner_goals"] == 1
        assert status["database_schema_version"] == 1
    finally:
        source.__exit__(None, None, None)
        target.__exit__(None, None, None)


def test_restore_requires_explicit_confirmation_and_rejects_wrong_format(tmp_path: Path) -> None:
    client = client_for(tmp_path / "safe-restore.sqlite3")
    try:
        client.put("/api/profile", json={"display_name": "Keep this data"})
        backup = client.get("/api/data/export").json()
        missing_confirmation = client.post("/api/data/restore", json=backup)
        assert missing_confirmation.status_code == 400
        wrong_format = client.post("/api/data/restore", json={
            **backup, "confirm_replace": True, "format": "other-app",
        })
        assert wrong_format.status_code == 400
        assert client.get("/api/profile").json()["profile"]["display_name"] == "Keep this data"
    finally:
        client.__exit__(None, None, None)


def test_restore_rejects_broken_foreign_keys_without_replacing_existing_data(tmp_path: Path) -> None:
    client = client_for(tmp_path / "broken-restore.sqlite3")
    try:
        client.put("/api/profile", json={"display_name": "Keep this data"})
        backup = client.get("/api/data/export").json()
        backup["tables"]["answers"].append({
            "id": "broken-answer", "session_id": "missing-session", "question_id": "q1",
            "answer_text": "bad reference", "position": 0, "created_at": "2026-01-01T00:00:00+00:00",
        })
        response = client.post("/api/data/restore", json={**backup, "confirm_replace": True})
        assert response.status_code == 422
        assert client.get("/api/profile").json()["profile"]["display_name"] == "Keep this data"
    finally:
        client.__exit__(None, None, None)


def test_restore_rejects_oversized_and_unexpected_table_data(tmp_path: Path) -> None:
    client = client_for(tmp_path / "invalid-restore.sqlite3")
    try:
        backup = client.get("/api/data/export").json()
        backup["tables"]["unexpected"] = []
        unexpected = client.post("/api/data/restore", json={**backup, "confirm_replace": True})
        assert unexpected.status_code == 400
        oversized = client.post("/api/data/restore", content=b" " * (25 * 1024 * 1024 + 1))
        assert oversized.status_code == 413
    finally:
        client.__exit__(None, None, None)


def test_security_headers_and_local_origin_guard(tmp_path: Path) -> None:
    client = client_for(tmp_path / "security.sqlite3")
    try:
        response = client.get("/api/health")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["cache-control"] == "no-store"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        denied = client.put("/api/profile", headers={"Origin": "http://attacker.example"}, json={"primary_goal": "english_fluency"})
        assert denied.status_code == 403
        assert client.get("/api/profile").json()["configured"] is False
    finally:
        client.__exit__(None, None, None)


def test_host_header_guard_rejects_non_local_hosts(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "host.sqlite3"), base_url="http://attacker.example")
    with client:
        response = client.get("/api/health")
        assert response.status_code == 400
