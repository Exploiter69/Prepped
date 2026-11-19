from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from prepped.learning import DEFAULT_CURRICULUM_PATH
from prepped.progress import initialize_progress_database

from fastapi.testclient import TestClient

from prepped.main import create_app


def client_for(path: Path) -> TestClient:
    client = TestClient(create_app(db_path=path))
    client.__enter__()
    return client


def complete_sentence_lesson(client: TestClient, lesson_id: str = "sentence-building") -> None:
    attempt = client.post("/api/learning/attempts", json={"lesson_id": lesson_id}).json()
    curriculum = json.loads(DEFAULT_CURRICULUM_PATH.read_text(encoding="utf-8"))
    lesson = next(item for item in curriculum["lessons"] if item["id"] == lesson_id)
    for exercise in lesson["exercises"]:
        if exercise["type"] in {"choice", "vocabulary", "listening"}:
            answer = exercise["answer"]
        elif exercise["type"] == "ordering":
            answer = exercise["answer"]
        else:
            answer = "I built and tested a small feature for my project."
        result = client.post(f"/api/learning/attempts/{attempt['id']}/responses", json={
            "exercise_id": exercise["id"], "answer": answer,
        })
        assert result.status_code == 200


def test_progress_overview_is_evidence_based_and_excludes_diagnostic(tmp_path: Path) -> None:
    client = client_for(tmp_path / "progress.sqlite3")
    try:
        initial = client.get("/api/progress/overview")
        assert initial.status_code == 200
        assert initial.json()["summary"]["lessons_completed"] == 0
        assert initial.json()["skills"]
        assert initial.json()["weekly_activity"][-1]["date"]
        assert any("not proficiency" in note.lower() for note in initial.json()["notes"])

        complete_sentence_lesson(client)
        completed = client.get("/api/progress/overview").json()
        assert completed["summary"]["lessons_completed"] == 1
        skill = next(item for item in completed["skills"] if item["skill_id"] == "english.sentence-structure")
        assert skill["completed_lessons"] == 1
        assert skill["evidence"][0]["title"] == "Build a clear sentence"

        complete_sentence_lesson(client, "baseline-check")
        after_diagnostic = client.get("/api/progress/overview").json()
        assert after_diagnostic["summary"]["lessons_completed"] == 1
        assert all(item["skill_id"] != "diagnostic" for item in after_diagnostic["skills"])
    finally:
        client.__exit__(None, None, None)


def test_goals_validate_create_count_archive_restore_and_delete(tmp_path: Path) -> None:
    client = client_for(tmp_path / "goals.sqlite3")
    try:
        invalid = client.post("/api/goals", json={"title": " ", "goal_type": "lessons_completed", "target_count": 0})
        assert invalid.status_code == 422
        complete_sentence_lesson(client)
        created = client.post("/api/goals", json={
            "title": "  Finish three lessons  ", "description": "  Build a routine  ",
            "goal_type": "lessons_completed", "target_count": 3,
        })
        assert created.status_code == 201
        goal = created.json()["goal"]
        assert goal["title"] == "Finish three lessons"
        assert goal["description"] == "Build a routine"
        assert goal["current_count"] == 0
        assert goal["remaining"] == 3

        complete_sentence_lesson(client, "grammar-in-context")
        refreshed = client.get("/api/goals").json()["goals"][0]
        assert refreshed["current_count"] == 1
        assert refreshed["remaining"] == 2

        updated = client.put(f"/api/goals/{goal['id']}", json={
            "title": "Finish two lessons", "goal_type": "lessons_completed", "target_count": 2,
        })
        assert updated.status_code == 200
        assert updated.json()["goal"]["reached_target"] is False
        assert client.post(f"/api/goals/{goal['id']}/archive").status_code == 200
        assert client.get("/api/goals").json()["count"] == 0
        assert client.get("/api/goals?include_archived=true").json()["count"] == 1
        assert client.post(f"/api/goals/{goal['id']}/restore").status_code == 200
        assert client.get("/api/goals").json()["count"] == 1
        assert client.delete(f"/api/goals/{goal['id']}").status_code == 204
        assert client.delete(f"/api/goals/{goal['id']}").status_code == 404
    finally:
        client.__exit__(None, None, None)


def test_progress_recommendations_follow_profile_and_saved_activity(tmp_path: Path) -> None:
    client = client_for(tmp_path / "recommendations.sqlite3")
    try:
        client.put("/api/profile", json={"primary_goal": "english_fluency", "improvement_areas": ["grammar"]})
        overview = client.get("/api/progress/overview").json()
        lesson = next(item for item in overview["recommendations"] if item["kind"] == "lesson")
        assert lesson["target_id"] == "sentence-building"
        assert "english fluency" in lesson["reason"].lower() or "grammar" in lesson["reason"].lower()
        goal = client.post("/api/goals", json={
            "title": "Review notes", "goal_type": "memory_reviews", "target_count": 5,
        }).json()["goal"]
        practice = client.post("/api/sessions").json()
        studios = client.get("/api/career/studios").json()["studios"]
        interview = client.post("/api/career/sessions", json={"studio_id": studios[0]["id"]}).json()
        updated = client.get("/api/progress/overview").json()
        assert any(item["kind"] == "goal" and item["target_id"] == goal["id"] for item in updated["recommendations"])
        assert any(item["kind"] == "resume_practice" and item["target_id"] == practice["id"] for item in updated["recommendations"])
        assert any(item["kind"] == "resume_interview" and item["target_id"] == interview["id"] for item in updated["recommendations"])
        recommendation = next(item for item in updated["recommendations"] if item["kind"] == "resume_practice")
        assert client.post("/api/progress/recommendations/dismiss", json={**recommendation, "title": " "}).status_code == 422
        assert client.post("/api/progress/recommendations/restore", json={
            "kind": "resume_practice", "target_id": " ",
        }).status_code == 422
        dismissed = client.post("/api/progress/recommendations/dismiss", json=recommendation)
        assert dismissed.status_code == 200
        assert not any(item["kind"] == "resume_practice" for item in client.get("/api/progress/overview").json()["recommendations"])
        hidden = client.get("/api/progress/recommendations/dismissed").json()["recommendations"]
        assert any(item["target_id"] == practice["id"] for item in hidden)
        restored = client.post("/api/progress/recommendations/restore", json={
            "kind": "resume_practice", "target_id": practice["id"],
        })
        assert restored.status_code == 200
        assert any(item["kind"] == "resume_practice" and item["target_id"] == practice["id"]
                   for item in client.get("/api/progress/overview").json()["recommendations"])
    finally:
        client.__exit__(None, None, None)


def test_goal_baseline_column_migration_preserves_existing_goal(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-goals.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE learner_goals (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            goal_type TEXT NOT NULL, target_count INTEGER NOT NULL, due_date TEXT,
            status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute(
            "INSERT INTO learner_goals (id,title,goal_type,target_count,created_at,updated_at) VALUES ('legacy','Old goal','lessons_completed',3,'2026-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00')"
        )
    initialize_progress_database(db_path)
    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(learner_goals)")}
        row = conn.execute("SELECT id,baseline_count FROM learner_goals WHERE id='legacy'").fetchone()
        assert "baseline_count" in columns
        assert row == ("legacy", 0)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 3
