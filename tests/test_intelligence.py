from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app
from prepped.learning import load_curriculum


def client_for(path: Path) -> TestClient:
    client = TestClient(create_app(db_path=path))
    client.__enter__()
    return client


def complete_sentence_lesson(client: TestClient, lesson_id: str = "sentence-building") -> dict:
    attempt = client.post("/api/learning/attempts", json={"lesson_id": lesson_id})
    assert attempt.status_code == 201
    result = attempt.json()
    raw_lesson = next(item for item in load_curriculum()["lessons"] if item["id"] == lesson_id)
    for exercise in raw_lesson["exercises"]:
        if exercise["type"] in {"choice", "vocabulary", "listening", "ordering"}:
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
            exercise = next(item for item in load_curriculum()["lessons"] if item["id"] == "sentence-building")["exercises"][0]
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


def test_mixed_closed_exercise_outcomes_are_not_collapsed_into_a_single_score(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-mixed.sqlite3")
    try:
        raw_lesson = next(item for item in load_curriculum()["lessons"] if item["id"] == "sentence-building")
        exercise = raw_lesson["exercises"][0]
        wrong = next(option["id"] for option in exercise["options"] if option["id"] != exercise["answer"])
        for answer in (exercise["answer"], wrong):
            attempt = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
            result = client.post(f"/api/learning/attempts/{attempt['id']}/responses", json={
                "exercise_id": exercise["id"], "answer": answer,
            })
            assert result.status_code == 200
        skill = next(item for item in client.get("/api/intelligence/overview").json()["skills"]
                     if item["skill_id"] == "english.sentence-structure")
        assert skill["state"] == "mixed_closed_exercise_evidence"
        assert skill["correct_response_count"] == 1
        assert skill["review_needed_count"] == 1
        assert "score" not in skill
    finally:
        client.__exit__(None, None, None)


def test_project_and_career_memory_reviews_link_to_their_practice_skills(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-career-provenance.sqlite3")
    try:
        project = client.post("/api/sessions")
        assert project.status_code == 201
        project_id = project.json()["id"]
        career = client.post("/api/career/sessions", json={"studio_id": "hr-behavioural"})
        assert career.status_code == 201, career.text
        career_id = career.json()["id"]
        for source_type, source_id, front in (
            ("practice", project_id, "Project practice correction"),
            ("career_interview", career_id, "Interview practice correction"),
        ):
            memory = client.post("/api/memory/items", json={
                "item_type": "correction", "front": front, "back": "Review the saved example.",
                "source_type": source_type, "source_id": source_id, "source_title": front,
            }).json()["item"]
            assert client.post(f"/api/memory/items/{memory['id']}/review", json={"rating": "good"}).status_code == 200
        skills = client.get("/api/intelligence/overview").json()["skills"]
        project_skill = next(item for item in skills if item["skill_id"] == "communication.project-summary")
        career_skill = next(item for item in skills if item["skill_id"] == "interview.hr-behavioural")
        assert any(item["kind"] == "revision_activity" for item in project_skill["evidence"])
        assert career_skill["curriculum_status"] == "active"
        assert career_skill["state"] == "practice_recorded"
        assert career_skill["closed_response_count"] == 0
        assert any(item["kind"] == "revision_activity" for item in career_skill["evidence"])
        today_activity = next(item for item in client.get("/api/intelligence/overview").json()["activity_30_days"]
                              if item["date"] == date.today().isoformat())
        assert today_activity["count"] >= 4
    finally:
        client.__exit__(None, None, None)


def test_linked_learner_memory_reviews_appear_as_revision_activity_not_mastery(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-revision.sqlite3")
    try:
        attempt = complete_sentence_lesson(client)
        memory = client.post("/api/memory/items", json={
            "item_type": "correction", "front": "Use a complete sentence",
            "back": "Include a subject and a finite verb.",
            "source_type": "lesson_attempt", "source_id": attempt["id"],
            "source_title": "Build a clear sentence",
        }).json()["item"]
        reviewed = client.post(f"/api/memory/items/{memory['id']}/review", json={"rating": "good"})
        assert reviewed.status_code == 200
        skill = next(item for item in client.get("/api/intelligence/overview").json()["skills"]
                     if item["skill_id"] == "english.sentence-structure")
        assert any(item["kind"] == "revision_activity" and item["outcome"] == "good"
                   for item in skill["evidence"])
        assert skill["correct_response_count"] == 2
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


def test_regeneration_preserves_completed_and_skipped_items_and_moves_forward(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-regenerate.sqlite3")
    try:
        client.put("/api/profile", json={"primary_goal": "english_fluency"})
        target = date.today().isoformat()
        first = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 60,
        }).json()["plan"]
        first_lesson = next(item for item in first["items"] if item["item_type"] == "lesson")
        complete_sentence_lesson(client, first_lesson["target_id"])
        added = client.post("/api/intelligence/plan/items", json={
            "plan_date": target, "item_type": "career_practice", "target_id": "hr-behavioural",
        }).json()["plan"]
        skipped = next(item for item in added["items"] if item["target_id"] == "hr-behavioural")
        client.patch(f"/api/intelligence/plan/items/{skipped['id']}", json={"skipped": True})
        regenerated = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 60, "regenerate": True,
        }).json()["plan"]
        preserved_lesson = next(item for item in regenerated["items"] if item["id"] == first_lesson["id"])
        preserved_skip = next(item for item in regenerated["items"] if item["id"] == skipped["id"])
        assert preserved_lesson["status"] == "completed"
        assert preserved_skip["status"] == "skipped"
        assert any(item["item_type"] == "lesson" and item["target_id"] != first_lesson["target_id"]
                   for item in regenerated["items"])
    finally:
        client.__exit__(None, None, None)


def test_long_memory_front_is_safe_in_adaptive_recommendation_dismissal(tmp_path: Path) -> None:
    db_path = tmp_path / "intelligence-long-memory.sqlite3"
    client = client_for(db_path)
    try:
        memory = client.post("/api/memory/items", json={
            "item_type": "concept", "front": "A" * 240, "back": "A short explanation.",
        }).json()["item"]
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE learning_memory SET due_at='2000-01-01T00:00:00+00:00' WHERE id=?", (memory["id"],))
        recommendation = next(item for item in client.get("/api/intelligence/overview").json()["recommendations"]
                              if item["kind"] == "review_memory")
        assert len(recommendation["title"]) <= 160
        dismissed = client.post("/api/intelligence/recommendations/dismiss", json={
            key: recommendation[key] for key in ("kind", "target_id", "title", "reason")
        })
        assert dismissed.status_code == 200
    finally:
        client.__exit__(None, None, None)


def test_regeneration_with_smaller_budget_preserves_completed_work_without_overflow(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-smaller-budget.sqlite3")
    try:
        client.put("/api/profile", json={"primary_goal": "english_fluency"})
        target = date.today().isoformat()
        initial = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 30,
        }).json()["plan"]
        lesson = next(item for item in initial["items"] if item["item_type"] == "lesson")
        complete_sentence_lesson(client, lesson["target_id"])
        regenerated = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 5, "regenerate": True,
        })
        assert regenerated.status_code == 200, regenerated.text
        plan = regenerated.json()["plan"]
        assert plan["available_minutes"] == 5
        assert next(item for item in plan["items"] if item["id"] == lesson["id"])["status"] == "completed"
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
        assert any(item["status"] == "skipped" and item["target_id"] == "hr-behavioural"
                   for item in updated.json()["plan"]["items"])
        assert client.post("/api/intelligence/plan/items", json={
            "plan_date": target, "item_type": "lesson", "target_id": "not-a-lesson",
        }).status_code == 404
    finally:
        client.__exit__(None, None, None)


def test_active_practice_goal_influences_recommendations_and_daily_plan(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-goal.sqlite3")
    try:
        client.put("/api/profile", json={"primary_goal": "english_fluency"})
        goal = client.post("/api/goals", json={
            "title": "Practise project explanations", "goal_type": "practice_sessions", "target_count": 3,
        }).json()["goal"]
        overview = client.get("/api/intelligence/overview").json()
        suggestion = next(item for item in overview["recommendations"]
                          if item["kind"] == "project_practice")
        assert suggestion["source"] == "active_learner_goal"
        assert goal["id"] == suggestion["goal_id"]
        preference = {key: suggestion[key] for key in ("kind", "target_id", "title", "reason")}
        assert client.post("/api/intelligence/recommendations/dismiss", json=preference).status_code == 200
        assert client.post("/api/progress/recommendations/restore", json={
            "kind": preference["kind"], "target_id": preference["target_id"],
        }).status_code == 200
        plan = client.post("/api/intelligence/plan/generate", json={
            "plan_date": date.today().isoformat(), "available_minutes": 60,
        }).json()["plan"]
        assert any(item["item_type"] == "project_practice" for item in plan["items"])
    finally:
        client.__exit__(None, None, None)


def test_manual_plan_addition_cannot_exceed_available_time(tmp_path: Path) -> None:
    client = client_for(tmp_path / "intelligence-budget.sqlite3")
    try:
        target = date.today().isoformat()
        created = client.post("/api/intelligence/plan/generate", json={
            "plan_date": target, "available_minutes": 5,
        })
        assert created.status_code == 200
        rejected = client.post("/api/intelligence/plan/items", json={
            "plan_date": target, "item_type": "career_practice", "target_id": "hr-behavioural",
        })
        assert rejected.status_code == 422
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
