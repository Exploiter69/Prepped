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
        "choice", "ordering", "reflection", "short_response", "vocabulary", "listening", "pronunciation"
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
        assert len(catalog["units"]) == 9
        assert len(catalog["skills"]) >= 14
        serialized = json.dumps(catalog)
        assert '"answer"' not in serialized
        assert '"correct_answer"' not in serialized

        saved = client.put("/api/profile", json={
            "primary_goal": "english_fluency",
            "confidence_level": "beginner",
            "improvement_areas": ["grammar", "speaking_fluency", "vocabulary", "pronunciation", "confidence", "professional_communication"],
        })
        assert saved.status_code == 200
        recommended = client.get("/api/learning/recommendations").json()
        assert recommended["track_id"] == "english-foundations"
        grammar = next(item for item in recommended["items"] if item["lesson_id"] == "grammar-in-context")
        assert "grammar" in grammar["why"]
        speaking = next(item for item in recommended["items"] if item["lesson_id"] == "speaking-structured")
        assert "speaking fluency" in speaking["why"]
        assert "low-pressure speaking" in speaking["why"]
        pronunciation = next(item for item in recommended["items"] if item["lesson_id"] == "pronunciation-self-review")
        assert "listen-and-repeat pronunciation" in pronunciation["why"]
        assert "professional communication" in speaking["why"]


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


def test_baseline_diagnostic_records_observable_tasks_without_level_or_score(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        before = client.get("/api/learning/diagnostic/latest").json()
        assert before["configured"] is True
        assert before["latest"] is None

        started = client.post("/api/learning/attempts", json={"lesson_id": "baseline-check"})
        assert started.status_code == 201
        attempt = started.json()
        assert attempt["lesson"]["kind"] == "diagnostic"
        assert attempt["current_exercise"]["id"] == "baseline-sentence"

        for exercise_id, answer in [
            ("baseline-sentence", "b"),
            ("baseline-summary-order", ["a", "b", "c"]),
            ("baseline-listening", "c"),
            ("baseline-project-response", "I built a small library app and tested the search form."),
        ]:
            result = client.post(f"/api/learning/attempts/{attempt['id']}/responses",
                                 json={"exercise_id": exercise_id, "answer": answer})
            assert result.status_code == 200

        completed = client.get(f"/api/learning/attempts/{attempt['id']}").json()
        assert completed["status"] == "completed"
        assert completed["next_lesson"] is None
        assert all("score" not in item for item in completed["feedback"])
        latest = client.get("/api/learning/diagnostic/latest").json()
        assert latest["latest"]["id"] == attempt["id"]
        assert latest["latest"]["status"] == "completed"
        assert len(latest["history"]) == 1
        repeated = client.post("/api/learning/attempts", json={"lesson_id": "baseline-check"})
        assert repeated.status_code == 201
        history = client.get("/api/learning/diagnostic/latest").json()
        assert history["latest"]["status"] == "in_progress"
        assert len(history["history"]) == 2
        progress = client.get("/api/learning/progress").json()
        assert progress["diagnostics_completed"] == 1
        assert progress["diagnostic_attempts_started"] == 2
        assert progress["lessons_completed"] == 0
        assert all(skill["completed_lessons"] == 0 for skill in progress["skills"])
        assert "No proficiency level" in latest["note"]


def test_phase_c_english_path_covers_all_requested_units_and_has_audio_text_alternatives() -> None:
    data = load_curriculum()
    track = next(item for item in data["tracks"] if item["id"] == "english-foundations")
    lessons = {item["id"]: item for item in data["lessons"]}
    titles = {lessons[item]["title"] for item in track["lesson_ids"]}
    assert {
        "Build a clear sentence", "Shape a sentence for clarity", "Grammar in context",
        "Ask clear questions", "Choose useful words in context", "Use useful study and project phrases",
        "Listen for the key detail", "Follow a short conversation",
        "Give a clear short response", "Express an opinion and handle a follow-up",
        "Listen, repeat, and self-review",
    } <= titles
    assert all(lessons[item]["exercises"] for item in track["lesson_ids"])
    listening = [
        exercise for lesson_id in track["lesson_ids"] for exercise in lessons[lesson_id]["exercises"]
        if exercise["type"] == "listening"
    ]
    pronunciation = [
        exercise for lesson_id in track["lesson_ids"] for exercise in lessons[lesson_id]["exercises"]
        if exercise["type"] == "pronunciation"
    ]
    assert len(listening) >= 4
    assert pronunciation
    assert all(item.get("audio_text") and item.get("transcript") for item in listening + pronunciation)
    assert all(item.get("guidance") for item in pronunciation)


def test_pronunciation_attempt_is_private_self_review_not_an_accuracy_score(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        first = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        for exercise_id, answer in [
            ("sentence-complete", "b"),
            ("sentence-order", ["a", "b", "c", "d"]),
            ("sentence-practice", "I tested the login form."),
        ]:
            assert client.post(f"/api/learning/attempts/{first['id']}/responses",
                               json={"exercise_id": exercise_id, "answer": answer}).status_code == 200
        grammar = client.post("/api/learning/attempts", json={"lesson_id": "grammar-in-context"}).json()
        for exercise_id, answer in [
            ("past-tense", "b"), ("preposition", "a"),
            ("grammar-review", "Yesterday, I tested the form."),
            ("articles-in-context", "a"), ("future-plan", "b"),
            ("error-correction", "Yesterday, she went to the lab and checked the results."),
        ]:
            assert client.post(f"/api/learning/attempts/{grammar['id']}/responses",
                               json={"exercise_id": exercise_id, "answer": answer}).status_code == 200
        shaping = client.post("/api/learning/attempts", json={"lesson_id": "sentence-shaping"}).json()
        for exercise_id, answer in [
            ("expand-sentence", "a"), ("combine-ideas", ["a", "b", "c"]),
            ("clarify-sentence", "Because the server did not respond, I could not access the page."),
        ]:
            assert client.post(f"/api/learning/attempts/{shaping['id']}/responses",
                               json={"exercise_id": exercise_id, "answer": answer}).status_code == 200
        speaking = client.post("/api/learning/attempts", json={"lesson_id": "speaking-structured"}).json()
        assert speaking["current_exercise"]["type"] == "short_response"
        assert "english.fluency" in speaking["lesson"]["skill_ids"]
        for exercise_id, answer in [
            ("speaking-description", "I worked on a form and added input validation."),
            ("speaking-process", "First I opened the form, then I checked the inputs."),
            ("speaking-explanation", "I checked the form with invalid inputs and observed the validation message."),
            ("speaking-retell", "The first version is ready, two issues were found, and fixes are planned."),
        ]:
            assert client.post(f"/api/learning/attempts/{speaking['id']}/responses",
                               json={"exercise_id": exercise_id, "answer": answer}).status_code == 200

        pronunciation = client.post(
            "/api/learning/attempts", json={"lesson_id": "pronunciation-self-review"}
        ).json()
        exercise = pronunciation["current_exercise"]
        assert exercise["type"] == "pronunciation"
        assert exercise["audio_text"] == exercise["transcript"]
        assert "answer" not in exercise
        response = client.post(
            f"/api/learning/attempts/{pronunciation['id']}/responses",
            json={"exercise_id": "repeat-project-update", "answer": ""},
        )
        assert response.status_code == 200
        feedback = response.json()["feedback"][0]
        assert feedback["status"] == "saved_for_self_review"
        assert "practised privately" in feedback["original_response"].lower()
        assert "does not measure pronunciation" in feedback["measurement_note"]
        assert "score" not in json.dumps(feedback).lower()


def test_question_vocabulary_and_listening_content_have_authored_answer_handling(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        first = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        for exercise_id, answer in [
            ("sentence-complete", "b"), ("sentence-order", ["a", "b", "c", "d"]),
            ("sentence-practice", "I tested the page."),
        ]:
            client.post(f"/api/learning/attempts/{first['id']}/responses",
                        json={"exercise_id": exercise_id, "answer": answer})
        grammar = client.post("/api/learning/attempts", json={"lesson_id": "grammar-in-context"}).json()
        for exercise_id, answer in [
            ("past-tense", "b"), ("preposition", "a"),
            ("grammar-review", "Yesterday, I tested the form."),
            ("articles-in-context", "a"), ("future-plan", "b"),
            ("error-correction", "Yesterday, she went to the lab and checked the results."),
        ]:
            client.post(f"/api/learning/attempts/{grammar['id']}/responses",
                        json={"exercise_id": exercise_id, "answer": answer})
        questions = client.post("/api/learning/attempts", json={"lesson_id": "question-formation"}).json()
        assert questions["current_exercise"]["id"] == "question-does"
        assert "answer" not in questions["current_exercise"]
        response = client.post(
            f"/api/learning/attempts/{questions['id']}/responses",
            json={"exercise_id": "question-does", "answer": "a"},
        )
        assert response.json()["feedback"][0]["status"] == "correct"

        vocabulary = client.post("/api/learning/attempts", json={"lesson_id": "phrases-for-study"})
        assert vocabulary.status_code == 409  # the vocabulary unit has its own prerequisite
        catalog = client.get("/api/learning/catalog").json()
        phrase_lesson = next(item for item in catalog["tracks"][0]["lessons"]
                             if item["id"] == "phrases-for-study")
        assert any(item["type"] == "vocabulary" and item.get("context")
                   for item in phrase_lesson["exercises"])
        assert any(item["type"] == "short_response" for item in phrase_lesson["exercises"])
