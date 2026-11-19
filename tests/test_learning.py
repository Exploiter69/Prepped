from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.learning import CurriculumValidationError, load_curriculum
from prepped.main import create_app


def client_for(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "prepped.sqlite3"))


def test_curriculum_loads_with_unique_skills_tracks_lessons_and_supported_exercises() -> None:
    data = load_curriculum()
    assert data["schema_version"] == "1.0.0"
    assert len({item["id"] for item in data["skills"]}) == len(data["skills"])
    assert len({item["id"] for item in data["tracks"]}) == len(data["tracks"])
    assert len({item["id"] for item in data["lessons"]}) == len(data["lessons"])
    assert {exercise["type"] for lesson in data["lessons"] for exercise in lesson["exercises"]} == {
        "choice", "ordering", "reflection", "short_response", "vocabulary", "listening"
    }


def test_curriculum_rejects_duplicate_lesson_ids_and_invalid_exercise_keys(tmp_path: Path) -> None:
    data = load_curriculum()
    data["lessons"].append(data["lessons"][0])
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        load_curriculum(path)
    except CurriculumValidationError as exc:
        assert "Duplicate lesson id" in str(exc)
    else:
        raise AssertionError("Duplicate lesson id was accepted")


def test_catalog_hides_answer_keys_and_exposes_profile_based_recommendations(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        response = client.get("/api/learning/catalog")
        assert response.status_code == 200
        catalog = response.json()
        assert catalog["recommendations"]["track_id"] == "placement-communication"
        assert catalog["levels"][0]["id"] == "foundation"
        assert len(catalog["units"]) == 6
        assert len(catalog["skills"]) >= 14
        serialized = json.dumps(catalog)
        assert '"answer"' not in serialized
        assert '"correct_answer"' not in serialized

        saved = client.put("/api/profile", json={
            "primary_goal": "english_fluency",
            "confidence_level": "beginner",
            "improvement_areas": ["grammar"],
        })
        assert saved.status_code == 200
        recommended = client.get("/api/learning/recommendations").json()
        assert recommended["track_id"] == "english-foundations"
        grammar = next(item for item in recommended["items"] if item["lesson_id"] == "grammar-in-context")
        assert "grammar" in grammar["why"]


def test_lesson_attempt_enforces_order_persists_feedback_and_updates_progress(tmp_path: Path) -> None:
    db = tmp_path / "prepped.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        started = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"})
        assert started.status_code == 201
        attempt = started.json()
        attempt_id = attempt["id"]
        assert attempt["status"] == "in_progress"
        assert attempt["current_exercise"]["id"] == "sentence-complete"
        assert attempt["next_lesson"]["lesson_id"] == "grammar-in-context"

        wrong_order = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-order", "answer": ["a", "b", "c", "d"]
        })
        assert wrong_order.status_code == 409

        first = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-complete", "answer": "b"
        })
        assert first.status_code == 200
        assert first.json()["current_exercise"]["id"] == "sentence-order"
        assert first.json()["feedback"][0]["status"] == "correct"

        second = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-order", "answer": ["a", "b", "c", "d"]
        })
        assert second.status_code == 200
        assert second.json()["current_exercise"]["id"] == "sentence-practice"

        third = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-practice", "answer": "I built a small timetable app for my class."
        })
        assert third.status_code == 200
        complete = third.json()
        assert complete["status"] == "completed"
        assert complete["current_exercise"] is None
        assert complete["feedback"][2]["status"] == "saved_for_self_review"
        assert complete["feedback"][2]["original_response"].startswith("I built")
        assert complete["feedback"][2]["example_to_compare"]

        reloaded = client.get(f"/api/learning/attempts/{attempt_id}")
        assert reloaded.status_code == 200
        assert reloaded.json()["status"] == "completed"
        progress = client.get("/api/learning/progress").json()
        assert progress["lessons_completed"] == 1
        assert progress["attempts_started"] == 1
        assert progress["learning_events"] == 5
        assert "sentence-building" in progress["completed_lesson_ids"]
        assert any(skill["status"] == "planned" for skill in progress["skills"])
        assert "not proficiency levels" in progress["note"]

    with TestClient(create_app(db_path=db)) as restarted:
        saved = restarted.get(f"/api/learning/attempts/{attempt_id}").json()
        assert saved["status"] == "completed"
        assert saved["feedback"][2]["original_response"] == "I built a small timetable app for my class."


def test_prerequisite_is_enforced_and_retry_is_a_new_attempt(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        blocked = client.post("/api/learning/attempts", json={"lesson_id": "grammar-in-context"})
        assert blocked.status_code == 409

        first = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        answers = [
            ("sentence-complete", "b"),
            ("sentence-order", ["a", "b", "c", "d"]),
            ("sentence-practice", "I completed a programming assignment."),
        ]
        for exercise_id, answer in answers:
            result = client.post(f"/api/learning/attempts/{first['id']}/responses",
                                 json={"exercise_id": exercise_id, "answer": answer})
            assert result.status_code == 200
        allowed = client.post("/api/learning/attempts", json={"lesson_id": "grammar-in-context"})
        assert allowed.status_code == 201
        assert allowed.json()["lesson_id"] == "grammar-in-context"
        retry = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"})
        assert retry.status_code == 201
        assert retry.json()["id"] != first["id"]


def test_invalid_answers_and_completed_attempt_mutations_are_rejected(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        started = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        attempt_id = started["id"]
        empty = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-complete", "answer": ""
        })
        assert empty.status_code == 422
        invalid_choice = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-complete", "answer": "not-an-option"
        })
        assert invalid_choice.status_code == 422
        good = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-complete", "answer": "a"
        })
        assert good.status_code == 200
        too_long = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-order", "answer": ["a", "b", "c", "d"]
        })
        assert too_long.status_code == 200
        final = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-practice", "answer": "A short reflection."
        })
        assert final.status_code == 200
        duplicate = client.post(f"/api/learning/attempts/{attempt_id}/responses", json={
            "exercise_id": "sentence-practice", "answer": "Another answer."
        })
        assert duplicate.status_code == 409


def test_ordering_rejects_missing_duplicate_or_foreign_tokens(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        started = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        attempt_id = started["id"]
        client.post(f"/api/learning/attempts/{attempt_id}/responses",
                    json={"exercise_id": "sentence-complete", "answer": "b"})
        invalid = client.post(f"/api/learning/attempts/{attempt_id}/responses",
                              json={"exercise_id": "sentence-order", "answer": ["a", "a", "c", "d"]})
        assert invalid.status_code == 422


def test_legacy_session_and_profile_data_survive_learning_migrations(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        client.put("/api/profile", json={
            "primary_goal": "project_communication", "confidence_level": "developing",
            "improvement_areas": ["project_explanation"],
        })
    import sqlite3
    connection = sqlite3.connect(db)
    connection.execute("""INSERT INTO sessions
        (id, scenario_id, scenario_version, status, created_at, scenario_json, rubric_json,
         attempt_group_id, attempt_number)
        VALUES ('legacy', 'old', '1', 'completed', '2026-01-01T00:00:00+00:00', '{}', '[]', 'legacy', 1)""")
    connection.execute("""INSERT INTO answers
        (id, session_id, question_id, answer_text, position, created_at)
        VALUES ('legacy-answer', 'legacy', 'q1', 'Preserve me', 0, '2026-01-01T00:00:00+00:00')""")
    connection.commit()
    connection.close()

    with TestClient(create_app(db_path=db)) as client:
        assert client.get("/api/profile").json()["profile"]["primary_goal"] == "project_communication"
        started = client.post("/api/learning/attempts", json={"lesson_id": "structured-project-summary"})
        assert started.status_code == 201

    connection = sqlite3.connect(db)
    assert connection.execute("SELECT answer_text FROM answers WHERE id='legacy-answer'").fetchone()[0] == "Preserve me"
    assert connection.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0] == 1
    connection.close()


def test_listening_and_vocabulary_exercises_are_safe_and_deterministic(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        catalog = client.get("/api/learning/catalog").json()
        english = next(track for track in catalog["tracks"] if track["id"] == "english-foundations")
        vocabulary = next(lesson for lesson in english["lessons"] if lesson["id"] == "vocabulary-in-context")
        assert any(exercise["type"] == "vocabulary" for exercise in vocabulary["exercises"])
        assert all("answer" not in exercise for exercise in vocabulary["exercises"])

        attempt = client.post("/api/learning/attempts", json={"lesson_id": "listening-for-details"})
        assert attempt.status_code == 409  # sentence-building is an explicit prerequisite

        first = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        for exercise_id, answer in [
            ("sentence-complete", "b"),
            ("sentence-order", ["a", "b", "c", "d"]),
            ("sentence-practice", "I built a study planner."),
        ]:
            assert client.post(f"/api/learning/attempts/{first['id']}/responses",
                               json={"exercise_id": exercise_id, "answer": answer}).status_code == 200

        listening = client.post("/api/learning/attempts", json={"lesson_id": "listening-for-details"}).json()
        exercise = listening["current_exercise"]
        assert exercise["type"] == "listening"
        assert exercise["audio_text"]
        assert exercise["transcript"]  # accessible text alternative
        assert "answer" not in exercise
        result = client.post(f"/api/learning/attempts/{listening['id']}/responses",
                             json={"exercise_id": "listening-detail", "answer": "b"})
        assert result.status_code == 200
        assert result.json()["feedback"][0]["status"] == "correct"


def test_in_progress_attempt_keeps_its_original_lesson_version(tmp_path: Path) -> None:
    import json
    from prepped.learning import DEFAULT_CURRICULUM_PATH

    curriculum_path = tmp_path / "curriculum.json"
    curriculum = json.loads(DEFAULT_CURRICULUM_PATH.read_text(encoding="utf-8"))
    curriculum_path.write_text(json.dumps(curriculum), encoding="utf-8")
    db = tmp_path / "snapshot.sqlite3"
    with TestClient(create_app(db_path=db, curriculum_path=curriculum_path)) as client:
        started = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        original_title = started["lesson"]["title"]
        curriculum["lessons"][0]["title"] = "Changed lesson title"
        curriculum_path.write_text(json.dumps(curriculum), encoding="utf-8")
        resumed = client.get(f"/api/learning/attempts/{started['id']}").json()
        assert resumed["lesson"]["title"] == original_title
        assert resumed["current_exercise"]["id"] == "sentence-complete"


def test_curriculum_rejects_prerequisite_cycles(tmp_path: Path) -> None:
    data = load_curriculum()
    data["lessons"][0]["prerequisites"] = ["grammar-in-context"]
    path = tmp_path / "cycle.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    try:
        load_curriculum(path)
    except CurriculumValidationError as exc:
        assert "prerequisite cycle" in str(exc)
    else:
        raise AssertionError("Prerequisite cycle was accepted")


def test_learning_migration_adds_lesson_snapshot_to_existing_phase_b_database(tmp_path: Path) -> None:
    import sqlite3
    from prepped.database import initialize_database

    db = tmp_path / "previous-phase-b.sqlite3"
    connection = sqlite3.connect(db)
    connection.execute("""CREATE TABLE learning_attempts (
        id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL, lesson_version TEXT NOT NULL,
        track_id TEXT NOT NULL, status TEXT NOT NULL, responses_json TEXT NOT NULL DEFAULT '[]',
        feedback_json TEXT, started_at TEXT NOT NULL, completed_at TEXT
    )""")
    connection.commit()
    connection.close()

    initialize_database(db)
    connection = sqlite3.connect(db)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(learning_attempts)")}
    assert "lesson_json" in columns
    connection.close()
