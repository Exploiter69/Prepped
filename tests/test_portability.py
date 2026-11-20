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
        practice = source.post("/api/sessions").json()
        source.post(f"/api/sessions/{practice['id']}/answers", json={
            "question_id": practice["current_question"]["id"],
            "answer_text": "I built a small local practice tool and tested its API.",
        })
        source.post("/api/learning/attempts", json={"lesson_id": "sentence-building"})
        studio = source.get("/api/career/studios").json()["studios"][0]
        interview = source.post("/api/career/sessions", json={"studio_id": studio["id"], "difficulty": "guided"}).json()
        source.post(f"/api/career/sessions/{interview['id']}/answers", json={"answer_text": "I worked on a student project and tested the main flow."})
        memory = source.post("/api/memory/items", json={
            "item_type": "phrase", "front": "Could you clarify?", "back": "A polite request for more detail.",
        }).json()["item"]
        source.post(f"/api/memory/items/{memory['id']}/review", json={"rating": "good"})
        source.post("/api/goals", json={
            "title": "Complete lessons", "goal_type": "lessons_completed", "target_count": 2,
        })
        source.post("/api/progress/recommendations/dismiss", json={
            "kind": "choose_goal", "target_id": "goals", "title": "Choose a small practice goal",
            "reason": "A short, learner-chosen target makes the next action clear.",
        })
        exported = source.get("/api/data/export")
        assert exported.status_code == 200
        assert exported.headers["content-type"].startswith("application/json")
        backup = exported.json()
        assert backup["format"] == "prepped-local-backup"
        assert set(backup["tables"]) == {
            "learner_profile", "sessions", "answers", "learning_attempts", "learning_events",
            "learning_memory", "learning_memory_reviews", "career_sessions", "career_turns", "learner_goals", "recommendation_dismissals",
        }
        assert backup["tables"]["sessions"]
        assert backup["tables"]["answers"]
        assert backup["tables"]["learning_attempts"]
        assert backup["tables"]["learning_events"]
        assert backup["tables"]["learning_memory"]
        assert backup["tables"]["learning_memory_reviews"]
        assert backup["tables"]["career_sessions"]
        assert backup["tables"]["career_turns"]
        assert backup["tables"]["learner_goals"]

        target.put("/api/profile", json={"display_name": "Target learner"})
        restore_payload = {**backup, "confirm_replace": True}
        restored = target.post("/api/data/restore", json=restore_payload)
        assert restored.status_code == 200, restored.text
        assert restored.json()["restored"] is True
        assert target.get("/api/profile").json()["profile"]["display_name"] == "Source learner"
        status = target.get("/api/data/status").json()
        assert status["counts"]["sessions"] == 1
        assert status["counts"]["answers"] == 1
        assert status["counts"]["learning_attempts"] == 1
        assert status["counts"]["learning_events"] == 1
        assert status["counts"]["learning_memory"] == 1
        assert status["counts"]["learning_memory_reviews"] == 1
        assert status["counts"]["career_sessions"] == 1
        assert status["counts"]["career_turns"] == 1
        assert status["counts"]["learner_goals"] == 1
        assert status["counts"]["recommendation_dismissals"] == 1
        assert status["database_schema_version"] == 3
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
        old_schema = client.post("/api/data/restore", json={
            **backup, "confirm_replace": True, "database_schema_version": 1,
        })
        assert old_schema.status_code == 409
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
        readiness = client.get("/api/ready")
        assert readiness.status_code == 200
        assert readiness.json()["status"] == "ready"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cross-origin-resource-policy"] == "same-origin"
        assert response.headers["cross-origin-opener-policy"] == "same-origin"
        assert response.headers["permissions-policy"] == "camera=(), microphone=(self), geolocation=()"
        policy = response.headers["content-security-policy"]
        assert "default-src 'self'" in policy
        assert "script-src 'self'" in policy
        assert "connect-src 'self'" in policy
        assert "frame-ancestors 'none'" in policy
        assert "access-control-allow-origin" not in response.headers
        assert client.get("/api/profile").headers["cache-control"] == "no-store"
        assert client.get("/api/data/export").headers["cache-control"] == "no-store"
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



def test_host_guard_rejects_malformed_authorities_without_server_error(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "malformed-host.sqlite3"))
    with client:
        malformed_hosts = ("[::1", "127.0.0.1:99999", "user@localhost")
        for host in malformed_hosts:
            response = client.get("/api/health", headers={"Host": host})
            assert response.status_code == 400, (host, response.status_code, response.text)


def test_origin_guard_rejects_malformed_and_non_origin_values(tmp_path: Path) -> None:
    client = client_for(tmp_path / "malformed-origin.sqlite3")
    try:
        for origin in ("http://[::1", "http://127.0.0.1:99999", "http://testserver/path", "http://user@testserver", "https://testserver"):
            response = client.put(
                "/api/profile",
                headers={"Origin": origin},
                json={"primary_goal": "english_fluency"},
            )
            assert response.status_code == 403, (origin, response.status_code, response.text)
        assert client.get("/api/profile").json()["configured"] is False
    finally:
        client.__exit__(None, None, None)


def test_same_origin_state_change_and_no_origin_local_client_remain_supported(tmp_path: Path) -> None:
    client = client_for(tmp_path / "valid-origin.sqlite3")
    try:
        same_origin = client.put(
            "/api/profile",
            headers={"Origin": "http://testserver"},
            json={"primary_goal": "english_fluency"},
        )
        assert same_origin.status_code == 200, same_origin.text
        no_origin = client.put(
            "/api/profile",
            json={"primary_goal": "placement_interviews"},
        )
        assert no_origin.status_code == 200, no_origin.text
    finally:
        client.__exit__(None, None, None)



def test_restore_rejects_non_finite_and_out_of_range_numbers_without_replacing_data(tmp_path: Path) -> None:
    client = client_for(tmp_path / "numeric-restore.sqlite3")
    try:
        client.put("/api/profile", json={"display_name": "Keep this data"})
        original = client.get("/api/data/export").json()

        non_finite = {**original, "confirm_replace": True}
        non_finite["tables"]["learner_profile"][0]["study_year"] = float("nan")
        rejected_nan = client.post("/api/data/restore", json=non_finite)
        assert rejected_nan.status_code == 422

        out_of_range = {**original, "confirm_replace": True}
        out_of_range["tables"]["learner_profile"][0]["study_year"] = 2**80
        rejected_integer = client.post("/api/data/restore", json=out_of_range)
        assert rejected_integer.status_code == 422

        assert client.get("/api/profile").json()["profile"]["display_name"] == "Keep this data"
    finally:
        client.__exit__(None, None, None)


def test_restore_rejects_excessively_nested_json_as_client_error(tmp_path: Path) -> None:
    client = client_for(tmp_path / "nested-restore.sqlite3")
    try:
        nested = b"[" * 1500 + b"0" + b"]" * 1500
        response = client.post("/api/data/restore", content=nested)
        assert response.status_code == 400
    finally:
        client.__exit__(None, None, None)



def test_readiness_fails_closed_when_a_required_table_is_missing(tmp_path: Path) -> None:
    database = tmp_path / "not-ready.sqlite3"
    client = client_for(database)
    try:
        with sqlite3.connect(database) as connection:
            connection.execute("DROP TABLE recommendation_dismissals")
        response = client.get("/api/ready")
        assert response.status_code == 503
        assert "not ready" in response.json()["detail"].lower()
    finally:
        client.__exit__(None, None, None)



def test_restore_enforces_record_count_and_content_length_limits(tmp_path: Path) -> None:
    client = client_for(tmp_path / "restore-limits.sqlite3")
    try:
        backup = client.get("/api/data/export").json()
        too_many = {**backup, "confirm_replace": True}
        too_many["tables"]["sessions"] = [{}] * 200_001
        row_limit = client.post("/api/data/restore", json=too_many)
        assert row_limit.status_code == 413

        malformed_length = client.post(
            "/api/data/restore",
            content=b"{}",
            headers={"Content-Length": "not-a-number"},
        )
        assert malformed_length.status_code == 400
    finally:
        client.__exit__(None, None, None)
