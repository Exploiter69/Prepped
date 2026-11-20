from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.career import load_studios
from prepped.main import create_app


def client_for(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "prepped.sqlite3"))


def start(client: TestClient, studio_id: str = "project-explanation", difficulty: str = "standard"):
    return client.post("/api/career/sessions", json={"studio_id": studio_id, "difficulty": difficulty})


def test_catalog_contains_three_data_driven_studios(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        result = client.get("/api/career/studios")
        assert result.status_code == 200
        studios = result.json()["studios"]
        assert {item["id"] for item in studios} == {
            "project-explanation", "hr-behavioural", "technical-fundamentals"
        }
        assert all(item["question_count"] == 4 for item in studios)
        assert client.get("/api/career/studios/unknown").status_code == 404


def test_start_validation_and_guided_followup_is_used(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        assert start(client, "unknown").status_code == 422
        assert start(client, difficulty="expert").status_code == 422
        created = start(client, difficulty="guided")
        assert created.status_code == 201
        session = created.json()
        assert session["current_prompt"]["turn_type"] == "primary"
        assert session["primary_question_count"] == 4

        blank = client.post(f"/api/career/sessions/{session['id']}/answers", json={"answer_text": "  "})
        assert blank.status_code == 422
        first = client.post(f"/api/career/sessions/{session['id']}/answers", json={
            "answer_text": "I built a campus tool for students. For example, students can find notices in one place."
        })
        assert first.status_code == 200
        assert first.json()["current_prompt"]["turn_type"] == "followup"
        assert "What problem were you trying to solve?" in first.json()["current_prompt"]["prompt"]
        second = client.post(f"/api/career/sessions/{session['id']}/answers", json={
            "answer_text": "For example, a student opens the feed and finds the latest notice."
        })
        assert second.json()["current_prompt"]["turn_type"] == "primary"
        assert second.json()["answered_primary_count"] == 1


def test_complete_interview_feedback_retry_history_and_restart_persistence(tmp_path: Path) -> None:
    db = tmp_path / "prepped.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        created = start(client, "technical-fundamentals", "challenging").json()
        session_id = created["id"]
        for index in range(4):
            primary = client.post(f"/api/career/sessions/{session_id}/answers", json={
                "answer_text": f"I would explain the concept with a concrete example. Because the trade-off matters, I would test it. I would also describe the expected result and compare it with a measured baseline before making a conclusion. Example {index}."
            })
            assert primary.status_code == 200
            assert primary.json()["current_prompt"]["turn_type"] == "followup"
            followup = client.post(f"/api/career/sessions/{session_id}/answers", json={
                "answer_text": "For example, I would inspect the query plan and measure the result because evidence matters."
            })
            assert followup.status_code == 200
        finished = client.get(f"/api/career/sessions/{session_id}").json()
        assert finished["status"] == "completed"
        assert finished["turn_count"] == 8
        assert finished["current_prompt"] is None
        feedback = client.get(f"/api/career/sessions/{session_id}/feedback").json()
        assert len(feedback["notes"]) == 8
        assert "not an expert interview rating" in feedback["disclaimer"]
        assert "overall_score" not in feedback
        assert feedback["notes"][0]["checks"][0]["observed"] is True
        assert client.post(f"/api/career/sessions/{session_id}/answers", json={"answer_text": "late"}).status_code == 409

        retry = client.post(f"/api/career/sessions/{session_id}/retry")
        assert retry.status_code == 201
        assert retry.json()["attempt_number"] == 2
        assert retry.json()["attempt_group_id"] == finished["attempt_group_id"]
        assert retry.json()["current_prompt"]["prompt"] == created["current_prompt"]["prompt"]
        history = client.get("/api/career/sessions").json()
        assert history["count"] == 2
        assert history["sessions"][0]["id"] == retry.json()["id"]

    with TestClient(create_app(db_path=db)) as restarted:
        restored = restarted.get(f"/api/career/sessions/{session_id}").json()
        assert restored["status"] == "completed"
        assert restored["turn_count"] == 8
        assert restarted.get(f"/api/career/sessions/{session_id}/feedback").status_code == 200


def test_resume_in_progress_session_and_delete_cascades_turns(tmp_path: Path) -> None:
    db = tmp_path / "prepped.sqlite3"
    with client_for(tmp_path) as client:
        session = start(client, "hr-behavioural").json()
        client.post(f"/api/career/sessions/{session['id']}/answers", json={"answer_text": "I worked with a team and helped deliver a task."})
        restored = client.get(f"/api/career/sessions/{session['id']}").json()
        assert restored["status"] == "in_progress"
        assert restored["current_prompt"]["turn_type"] == "followup"
        assert restored["turn_count"] == 1
        assert client.delete(f"/api/career/sessions/{session['id']}").status_code == 204
        assert client.get(f"/api/career/sessions/{session['id']}").status_code == 404
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM career_turns").fetchone()[0] == 0


def test_studio_catalog_is_versioned_and_has_authored_difficulty_followups() -> None:
    catalog = load_studios()
    assert catalog["version"]
    for studio in catalog["studios"]:
        for question in studio["questions"]:
            variants = question["followup"]["prompts"]
            assert set(variants) == {"guided", "standard", "challenging"}
            assert all(isinstance(value, str) and value.strip() for value in variants.values())
            contextual = question["contextual_followup"]
            assert contextual["trigger"]
            assert contextual["prompt"].strip()


def test_career_schema_is_additive_and_preserves_existing_practice(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        practice = client.post("/api/sessions")
        assert practice.status_code == 201
        practice_id = practice.json()["id"]
        career = start(client, "project-explanation")
        assert career.status_code == 201
        assert client.get(f"/api/sessions/{practice_id}").status_code == 200
        assert client.get(f"/api/career/sessions/{career.json()['id']}").status_code == 200
        assert client.delete(f"/api/career/sessions/{career.json()['id']}").status_code == 204
        assert client.get(f"/api/sessions/{practice_id}").status_code == 200


def test_difficulty_modes_select_distinct_authored_followups(tmp_path: Path) -> None:
    prompts = {}
    with client_for(tmp_path) as client:
        for difficulty in ("guided", "standard", "challenging"):
            session = start(client, difficulty=difficulty).json()
            response = client.post(
                f"/api/career/sessions/{session['id']}/answers",
                json={"answer_text": "For example, I built a student project and tested the main feature."},
            )
            assert response.status_code == 200
            prompts[difficulty] = response.json()["current_prompt"]["prompt"]
    assert len(set(prompts.values())) == 3
    assert "What problem were you trying to solve?" in prompts["guided"]
    assert "user journey" in prompts["standard"].lower() or "concrete user journey" in prompts["standard"].lower()
    assert "evidence" in prompts["challenging"].lower()



def test_contextual_followup_uses_authored_prompt_when_expected_cue_is_not_detected(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        session = start(client, "project-explanation", "guided").json()
        response = client.post(
            f"/api/career/sessions/{session['id']}/answers",
            json={"answer_text": "Our project helps students find campus notices in one place."},
        )
        assert response.status_code == 200
        prompt = response.json()["current_prompt"]
        assert "specific user journey" in prompt["prompt"].lower()
        assert "simple text cue was not detected" in prompt["context_note"].lower()

        with_example = start(client, "project-explanation", "guided").json()
        response = client.post(
            f"/api/career/sessions/{with_example['id']}/answers",
            json={"answer_text": "For example, a student opens the feed and finds a current notice."},
        )
        assert response.status_code == 200
        fallback = response.json()["current_prompt"]
        assert "what problem were you trying to solve" in fallback["prompt"].lower()
        assert "selected practice level" in fallback["context_note"].lower()


def test_career_feedback_has_one_evidence_grounded_coaching_action_per_turn(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        session = start(client, "project-explanation").json()
        session_id = session["id"]
        for index in range(4):
            first = client.post(
                f"/api/career/sessions/{session_id}/answers",
                json={"answer_text": f"I worked on the project feature {index} and helped the team."},
            )
            assert first.status_code == 200
            second = client.post(
                f"/api/career/sessions/{session_id}/answers",
                json={"answer_text": "The feature helps students complete a task with fewer steps."},
            )
            assert second.status_code == 200
        feedback = client.get(f"/api/career/sessions/{session_id}/feedback").json()
        assert len(feedback["notes"]) == 8
        coaching = feedback["notes"][0]["coaching"]
        assert "specific example" in coaching["action"].lower()
        assert "not detected" in coaching["basis"].lower()
        assert "overall_score" not in feedback
        assert "rating" not in feedback


def test_simpler_prompt_variant_is_saved_as_the_prompt_used_for_the_answer(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        session = start(client, "project-explanation").json()
        prompt = session["current_prompt"]
        assert prompt["simpler_prompt"] != prompt["prompt"]
        assert prompt["clarification"]
        response = client.post(
            f"/api/career/sessions/{session['id']}/answers",
            json={"answer_text": "I built a campus project for students.", "prompt_variant": "simplified"},
        )
        assert response.status_code == 200
        assert response.json()["turns"][0]["prompt"] == prompt["simpler_prompt"]


def test_retry_feedback_compares_previous_answers_without_claiming_improvement(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        first = start(client, "project-explanation").json()
        session_id = first["id"]
        for attempt_label in ("first", "second"):
            for index in range(4):
                primary = client.post(
                    f"/api/career/sessions/{session_id}/answers",
                    json={"answer_text": f"For example, I built the {attempt_label} feature {index} because it solved a user problem, and I tested it."},
                )
                assert primary.status_code == 200
                followup = client.post(
                    f"/api/career/sessions/{session_id}/answers",
                    json={"answer_text": f"For example, I tested the {attempt_label} change because reliability mattered and recorded the result."},
                )
                assert followup.status_code == 200
            if attempt_label == "first":
                retry = client.post(f"/api/career/sessions/{session_id}/retry")
                assert retry.status_code == 201
                session_id = retry.json()["id"]

        feedback = client.get(f"/api/career/sessions/{session_id}/feedback").json()
        assert len(feedback["attempt_comparison"]) == 8
        assert feedback["attempt_comparison"][0]["previous_answer"].startswith("For example, I built the first")
        assert feedback["attempt_comparison"][0]["current_answer"].startswith("For example, I built the second")
        assert "not a measured improvement" in feedback["comparison_note"].lower()
