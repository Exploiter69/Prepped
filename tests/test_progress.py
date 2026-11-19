from __future__ import annotations

import json
from pathlib import Path

from prepped.learning import DEFAULT_CURRICULUM_PATH

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
    for exercise in lesson["exercises"]
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

        complete_sentence_lesson(client)
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
        updated = client.get("/api/progress/overview").json()
        assert any(item["kind"] == "goal" and item["target_id"] == goal["id"] for item in updated["recommendations"])
    finally:
        client.__exit__(None, None, None)
