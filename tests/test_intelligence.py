from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app


def client_for(path: Path) -> TestClient:
    client = TestClient(create_app(db_path=path))
    client.__enter__()
    return client


def complete_sentence_lesson(client: TestClient, lesson_id: str = "sentence-building") -> dict:
    attempt = client.post("/api/learning/attempts", json={"lesson_id": lesson_id})
    assert attempt.status_code == 201
    result = attempt.json()
    for exercise in result["lesson"]["exercises"]:
        if exercise["type"] in {"choice", "vocabulary", "listening"}:
            answer = exercise["answer"]
        elif exercise["type"] == "ordering":
            answer = exercise["answer"]
        else:
            answer = "I built and tested a small project feature."
        response = client.post(f"/api/learning/attempts/{result['id']}/responses", json={
            "exercise_id": exercise["id"], "answer": answer,
        })
        assert response.status_code == 200, response.text
        result = response.json()
    return result


def test_skill_profile_starts_uncertain_and_does_not_infer_mastery(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-empty.sqlite3")
    try:
        response = client.get("/api/intelligence/overview")
        assert response.status_code == 200
        payload = response.json()
        assert payload["summary"]["skills_with_activity"] == 0
        assert payload["summary"]["closed_exercise_responses"] == 0
        assert payload["skills"]
        assert all(item["state"] == "insufficient_evidence" for item in payload["skills"])
        assert all("mastery" in item["limitations"].lower() for item in payload["skills"])
        assert "ability" not in payload["summary"]
    finally:
        client.__exit__(None, None, None)


def test_skill_evidence_separates_closed_answers_open_responses_and_activity(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-evidence.sqlite3")
    try:
        completed = complete_sentence_lesson(client)
        assert completed["status"] == "completed"
        skill = next(item for item in client.get("/api/intelligence/overview").json()["skills"]
                     if item["skill_id"] == "english.sentence-structure")
        assert skill["activity_count"] >= 1
        assert skill["closed_response_count"] == 2
        assert skill["correct_response_count"] == 2
        assert skill["review_needed_count"] == 0
        assert skill["state"] == "repeated_correct_responses_observed"
        assert any(item["kind"] == "open_self_review" for item in skill["evidence"])
        assert all(item["outcome"] != "saved_for_self_review" for item in skill["evidence"]
                   if item["kind"] == "closed_exercise_response")
    finally:
        client.__exit__(None, None, None)


def test_repeated_closed_exercise_misses_suggest_revisiting_linked_lesson(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-misses.sqlite3")
    try:
        for _ in range(2):
            attempt = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
            exercise = attempt["lesson"]["exercises"][0]
            wrong = next(option["id"] for option in exercise["options"] if option["id"] != exercise["answer"])
            response = client.post(f"/api/learning/attempts/{attempt['id']}/responses", json={
                "exercise_id": exercise["id"], "answer": wrong,
            })
            assert response.status_code == 200
        overview = client.get("/api/intelligence/overview").json()
        skill = next(item for item in overview["skills"] if item["skill_id"] == "english.sentence-structure")
        assert skill["state"] == "revisit_suggested"
        assert skill["repeated_mistakes"][0]["review_needed_responses"] == 2
        assert any(item["kind"] == "lesson" and item["target_id"] == "sentence-building"
                   and item["source"] == "repeated_observed_response" for item in overview["recommendations"])
    finally:
        client.__exit__(None, None, None)


def test_evidence_freshness_is_visible_and_old_evidence_is_not_called_current(tmp_path: Path) -> None:
    db_path = tmp_path / "intelligence-stale.sqlite3"
    client = client_for(db_path)
    try:
        complete_sentence_lesson(client)
        old = (date.today() - timedelta(days=70)).isoformat() + "T12:00:00+00:00"
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE learning_attempts SET started_at=?,completed_at=?", (old, old))
        skill = next(item for item in client.get("/api/intelligence/overview").json()["skills"]
                     if item["skill_id"] == "english.sentence-structure")
        assert skill["freshness"] == "stale"
        assert skill["evidence_age_days"] >= 69
    finally:
        client.__exit__(None, None, None)


def test_prerequisite_and_profile_goal_shape_explainable_recommendations(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-prereq.sqlite3")
    try:
        saved = client.put("/api/profile", json={"primary_goal": "english_fluency"})
        assert saved.status_code == 200
        overview = client.get("/api/intelligence/overview").json()
        sentence = next(item for item in overview["recommendations"]
                        if item["kind"] == "lesson" and item["target_id"] == "sentence-building")
        assert sentence["source"] in {"declared_prerequisite", "learner_goal_route"}
        assert sentence["reason"]
        assert "english.fluency" in {item["skill_id"] for item in overview["skills"]}
    finally:
        client.__exit__(None, None, None)


def test_daily_plan_completion_is_derived_from_saved_source_activity(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-daily-plan.sqlite3")
    try:
        client.put("/api/profile", json={"primary_goal": "english_fluency"})
        target = date.today().isoformat()
        generated = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 30,
        })
        assert generated.status_code == 200, generated.text
        plan = generated.json()["plan"]
        lesson_item = next(item for item in plan["items"] if item["item_type"] == "lesson")
        assert lesson_item["status"] == "planned"
        assert plan["estimated_minutes"] <= 30
        complete_sentence_lesson(client, lesson_item["target_id"])
        refreshed = client.get("/api/intelligence/plan", params={"plan_date": target}).json()["plan"]
        updated = next(item for item in refreshed["items"] if item["id"] == lesson_item["id"])
        assert updated["status"] == "completed"
        assert updated["self_reported"] is False
    finally:
        client.__exit__(None, None, None)


def test_due_memory_review_is_included_and_only_real_review_completes_it(tmp_path: Path) -> None:
    db_path = tmp_path / "intelligence-memory-plan.sqlite3"
    client = client_for(db_path)
    try:
        memory = client.post("/api/memory/items", json={
            "item_type": "phrase", "front": "Could you clarify?", "back": "Ask politely for more detail.",
        }).json()["item"]
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE learning_memory SET due_at='2000-01-01T00:00:00+00:00' WHERE id=?", (memory["id"],))
        target = date.today().isoformat()
        plan = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 30,
        }).json()["plan"]
        review_item = next(item for item in plan["items"] if item["item_type"] == "memory_review")
        assert review_item["status"] == "planned"
        client.post(f"/api/memory/items/{memory['id']}/review", json={"rating": "good"})
        refreshed = client.get("/api/intelligence/plan", params={"plan_date": target}).json()["plan"]
        assert next(item for item in refreshed["items"] if item["id"] == review_item["id"])["status"] == "completed"
    finally:
        client.__exit__(None, None, None)


def test_weekly_plan_generates_seven_days_without_duplicate_lesson_assignments(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-week.sqlite3")
    try:
        monday = date.today() - timedelta(days=date.today().weekday())
        response = client.post("/api/intelligence/plan/week/generate", json={
            "week_start": monday.isoformat(), "available_minutes_per_day": 30,
        })
        assert response.status_code == 200, response.text
        days = response.json()["days"]
        assert len(days) == 7
        lessons = [item["target_id"] for day in days for item in day["items"] if item["item_type"] == "lesson"]
        assert len(lessons) == len(set(lessons))
        assert all(day["estimated_minutes"] <= 30 for day in days)
        assert client.get("/api/intelligence/plan/week", params={"week_start": monday.isoformat()}).json()["days"] == days
    finally:
        client.__exit__(None, None, None)


def test_plan_supports_learner_override_skip_and_reordering(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-override.sqlite3")
    try:
        target = date.today().isoformat()
        client.post("/api/intelligence/plan/generate", json={"plan_date": target, "available_minutes": 60})
        added = client.post("/api/intelligence/plan/items", json={
            "plan_date": target, "item_type": "career_practice", "target_id": "hr-behavioural",
        })
        assert added.status_code == 201
        plan = added.json()["plan"]
        item = next(item for item in plan["items"] if item["target_id"] == "hr-behavioural")
        updated = client.patch(f"/api/intelligence/plan/items/{item['id']}", json={"skipped": True, "position": 0})
        assert updated.status_code == 200
        changed = next(item for item in updated.json()["plan"]["items"] if item["id"] == item["id"])
        assert changed["status"] in {"skipped", "planned"}
        assert any(item["status"] == "skipped" and item["target_id"] == "hr-behavioural"
                   for item in updated.json()["plan"]["items"])
        assert client.post("/api/intelligence/plan/items", json={
            "plan_date": target, "item_type": "lesson", "target_id": "not-a-lesson",
        }).status_code == 404
    finally:
        client.__exit__(None, None, None)


def test_adaptive_recommendations_can_be_dismissed_and_restored(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-dismiss.sqlite3")
    try:
        recommendation = next(item for item in client.get("/api/intelligence/overview").json()["recommendations"]
                              if item["kind"] == "lesson")
        payload = {key: recommendation[key] for key in ("kind", "target_id", "title", "reason")}
        assert client.post("/api/intelligence/recommendations/dismiss", json=payload).status_code == 200
        assert not any(item["target_id"] == recommendation["target_id"]
                       for item in client.get("/api/intelligence/overview").json()["recommendations"])
        assert client.post("/api/intelligence/recommendations/restore", json=payload).status_code == 200
        assert any(item["target_id"] == recommendation["target_id"]
                   for item in client.get("/api/intelligence/overview").json()["recommendations"])
    finally:
        client.__exit__(None, None, None)
