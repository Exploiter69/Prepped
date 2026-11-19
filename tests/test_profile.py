from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app


def client_for(path: Path) -> TestClient:
    client = TestClient(create_app(db_path=path))
    client.__enter__()
    return client


def test_profile_starts_unconfigured_and_can_be_saved_and_read(tmp_path: Path) -> None:
    db_path = tmp_path / "profile.sqlite3"
    client = client_for(db_path)
    try:
        initial = client.get("/api/profile")
        assert initial.status_code == 200
        assert initial.json() == {"configured": False, "profile": None}

        saved = client.put(
            "/api/profile",
            json={
                "display_name": "  Alok  ",
                "study_year": 3,
                "branch": "Computer Science and Engineering",
                "primary_goal": "project_communication",
                "confidence_level": "developing",
                "target_role": "Software Engineer",
                "improvement_areas": ["project_explanation", "technical_interviews"],
            },
        )
        assert saved.status_code == 200
        profile = saved.json()["profile"]
        assert saved.json()["configured"] is True
        assert profile["display_name"] == "Alok"
        assert profile["study_year"] == 3
        assert profile["primary_goal"] == "project_communication"
        assert profile["improvement_areas"] == ["project_explanation", "technical_interviews"]
        assert profile["created_at"] == profile["updated_at"]

        reread = client.get("/api/profile").json()["profile"]
        assert reread == profile
    finally:
        client.__exit__(None, None, None)


def test_profile_update_preserves_creation_time_and_replaces_preferences(tmp_path: Path) -> None:
    client = client_for(tmp_path / "profile.sqlite3")
    try:
        first = client.put("/api/profile", json={"primary_goal": "english_fluency"}).json()["profile"]
        second = client.put(
            "/api/profile",
            json={
                "display_name": "Learner",
                "primary_goal": "technical_interviews",
                "confidence_level": "confident",
                "improvement_areas": ["vocabulary"],
            },
        ).json()["profile"]
        assert second["created_at"] == first["created_at"]
        assert second["updated_at"] >= first["updated_at"]
        assert second["primary_goal"] == "technical_interviews"
        assert second["improvement_areas"] == ["vocabulary"]
    finally:
        client.__exit__(None, None, None)


def test_profile_persists_after_app_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "profile.sqlite3"
    first = client_for(db_path)
    try:
        response = first.put(
            "/api/profile",
            json={"primary_goal": "professional_communication", "study_year": 3},
        )
        assert response.status_code == 200
    finally:
        first.__exit__(None, None, None)

    second = client_for(db_path)
    try:
        profile = second.get("/api/profile").json()["profile"]
        assert profile["primary_goal"] == "professional_communication"
        assert profile["study_year"] == 3
    finally:
        second.__exit__(None, None, None)


def test_profile_rejects_invalid_values_and_oversized_fields(tmp_path: Path) -> None:
    client = client_for(tmp_path / "profile.sqlite3")
    try:
        invalid_goal = client.put("/api/profile", json={"primary_goal": "get_placed_guaranteed"})
        invalid_year = client.put("/api/profile", json={"study_year": 0})
        invalid_area = client.put("/api/profile", json={"improvement_areas": ["mind_reading"]})
        oversized_name = client.put("/api/profile", json={"display_name": "x" * 81})
        too_many_areas = client.put(
            "/api/profile",
            json={"improvement_areas": ["speaking_fluency"] * 10},
        )
        assert all(r.status_code == 422 for r in [invalid_goal, invalid_year, invalid_area, oversized_name, too_many_areas])
    finally:
        client.__exit__(None, None, None)


def test_profile_migration_keeps_existing_sessions_and_answers(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL, scenario_version TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT
            );
            CREATE TABLE answers (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                question_id TEXT NOT NULL, answer_text TEXT NOT NULL, position INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            INSERT INTO sessions (id, scenario_id, scenario_version, status, created_at)
            VALUES ('legacy-session', 'project-explanation', '1.0.0', 'completed', '2026-01-01T00:00:00+00:00');
            INSERT INTO answers (id, session_id, question_id, answer_text, position, created_at)
            VALUES ('legacy-answer', 'legacy-session', 'overview', 'Saved answer', 0, '2026-01-01T00:00:00+00:00');
            """
        )

    client = client_for(db_path)
    try:
        assert client.get("/api/profile").json() == {"configured": False, "profile": None}
        with sqlite3.connect(db_path) as connection:
            assert connection.execute("SELECT answer_text FROM answers WHERE id='legacy-answer'").fetchone()[0] == "Saved answer"
            assert connection.execute("SELECT id FROM sessions WHERE id='legacy-session'").fetchone()[0] == "legacy-session"
            assert connection.execute("SELECT COUNT(*) FROM learner_profile").fetchone()[0] == 0
    finally:
        client.__exit__(None, None, None)

def test_profile_page_exposes_accessible_toggle_and_serves_profile_handler(tmp_path: Path) -> None:
    client = client_for(tmp_path / "profile-ui.sqlite3")
    try:
        page = client.get("/")
        assert page.status_code == 200
        assert 'id="profile-edit-toggle"' in page.text
        assert 'aria-controls="profile-form"' in page.text
        assert 'aria-expanded="false"' in page.text
        assert 'id="profile-form"' in page.text
        assert 'class="profile-form hidden"' in page.text
        assert "/static/app.js" in page.text

        script = client.get("/static/app.js")
        assert script.status_code == 200
        assert "function setProfileFormOpen(open)" in script.text
        assert 'toggle.setAttribute("aria-expanded", String(open))' in script.text
        assert 'setProfileFormOpen($("#profile-form").classList.contains("hidden"))' in script.text
    finally:
        client.__exit__(None, None, None)

