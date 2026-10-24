from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app
from prepped.scenarios import load_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "scenarios" / "project-explanation.v1.json"


def make_client(tmp_path: Path) -> tuple[TestClient, Path]:
    db_path = tmp_path / "nested" / "test.sqlite3"
    client = TestClient(create_app(db_path=db_path, scenario_path=SCENARIO_PATH))
    client.__enter__()
    return client, db_path


def finish_session(client: TestClient, session_id: str, answers: list[str]) -> dict:
    session = client.get(f"/api/sessions/{session_id}").json()
    for answer in answers:
        question_id = session["current_question"]["id"]
        response = client.post(
            f"/api/sessions/{session_id}/answers",
            json={"question_id": question_id, "answer_text": answer},
        )
        assert response.status_code == 200, response.text
        session = response.json()
    return session


def test_health_homepage_and_database_initialization(tmp_path: Path) -> None:
    client, db_path = make_client(tmp_path)
    try:
        health = client.get("/api/health")
        home = client.get("/")
        css = client.get("/static/style.css")
        js = client.get("/static/app.js")

        assert health.status_code == 200
        assert health.json() == {"status": "ok", "application": "Prepped"}
        assert db_path.is_file()
        assert "Start practice" in home.text
        assert "practice flow and feedback engine are not implemented yet" not in home.text
        assert css.status_code == 200 and "color-scheme: dark" in css.text
        assert js.status_code == 200 and "/api/sessions" in js.text

        with sqlite3.connect(db_path) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"sessions", "answers"}.issubset(tables)
    finally:
        client.__exit__(None, None, None)


def test_scenario_endpoint_returns_versioned_scenario(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        response = client.get("/api/scenarios/project-explanation")
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["id"] == "project-explanation"
        assert scenario["version"] == "1.0.0"
        assert len(scenario["questions"]) == 5
        assert {item["id"] for item in scenario["rubric"]} == {
            "clarity", "structure", "specificity", "follow_up_handling", "conciseness",
        }
    finally:
        client.__exit__(None, None, None)


def test_full_practice_flow_feedback_retry_comparison_and_delete(tmp_path: Path) -> None:
    client, db_path = make_client(tmp_path)
    try:
        started = client.post("/api/sessions")
        assert started.status_code == 201
        session = started.json()
        first_id = session["id"]
        assert session["status"] == "in_progress"
        assert session["answered_count"] == 0
        assert session["current_question"]["id"] == "project_overview"

        premature_feedback = client.get(f"/api/sessions/{first_id}/feedback")
        assert premature_feedback.status_code == 409

        wrong_order = client.post(
            f"/api/sessions/{first_id}/answers",
            json={"question_id": "reflection", "answer_text": "This is out of order."},
        )
        assert wrong_order.status_code == 409

        answers = [
            "I built a campus notice tracker because students missed updates spread across channels. It helps students find current notices.",
            "I implemented the FastAPI endpoints and SQLite persistence. For example, I wrote tests for session creation and saving answers.",
            "I chose SQLite because this first version runs locally and needs no database server. I considered a hosted database but avoided a service dependency.",
            "I tested the session API and all five scenario questions locally. The tests passed, but I have not measured student outcomes.",
            "Next I would improve feedback after a small student pilot. I learned to separate observed test results from assumptions.",
        ]
        completed = finish_session(client, first_id, answers)
        assert completed["status"] == "completed"
        assert completed["answered_count"] == 5
        assert completed["current_question"] is None
        assert completed["completed_at"]

        feedback_response = client.get(f"/api/sessions/{first_id}/feedback")
        assert feedback_response.status_code == 200
        feedback = feedback_response.json()
        assert feedback["answered_questions"] == 5
        assert feedback["total_questions"] == 5
        assert len(feedback["question_feedback"]) == 5
        assert len(feedback["rubric_feedback"]) == 5
        assert "overall_score" not in feedback
        assert feedback["question_feedback"][0]["evidence"] == answers[0]
        assert feedback["rubric_feedback"][2]["evidence"]
        assert any("validated assessment" in item for item in feedback["limitations"])

        retry = client.post(f"/api/sessions/{first_id}/retry")
        assert retry.status_code == 201
        second = retry.json()
        assert second["id"] != first_id
        assert second["attempt_group_id"] == session["attempt_group_id"]
        assert second["attempt_number"] == 2
        assert second["scenario_version"] == session["scenario_version"]
        assert second["answered_count"] == 0

        second_answers = [
            "My project helps students find notices in one place.",
            "I built the API and tested its SQLite storage with pytest.",
            "I used SQLite because the app is local-first; a hosted database would add setup and cost.",
            "I ran five tests successfully, but I have not measured whether students miss fewer notices.",
            "I would test with students next. I learned to state limitations instead of claiming impact without evidence.",
        ]
        second_completed = finish_session(client, second["id"], second_answers)
        assert second_completed["status"] == "completed"
        second_feedback = client.get(f"/api/sessions/{second['id']}/feedback").json()
        assert second_feedback["attempt_number"] == 2

        history = client.get("/api/sessions").json()["sessions"]
        assert {item["id"] for item in history} >= {first_id, second["id"]}

        with sqlite3.connect(db_path) as connection:
            before = connection.execute("SELECT COUNT(*) FROM answers WHERE session_id = ?", (first_id,)).fetchone()[0]
        assert before == 5
        deleted = client.delete(f"/api/sessions/{first_id}")
        assert deleted.status_code == 204
        with sqlite3.connect(db_path) as connection:
            after = connection.execute("SELECT COUNT(*) FROM answers WHERE session_id = ?", (first_id,)).fetchone()[0]
            session_count = connection.execute("SELECT COUNT(*) FROM sessions WHERE id = ?", (first_id,)).fetchone()[0]
        assert after == 0
        assert session_count == 0
    finally:
        client.__exit__(None, None, None)


def test_skips_and_empty_answers_produce_not_enough_evidence(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        session = client.post("/api/sessions").json()
        completed = finish_session(client, session["id"], ["", " ", "", "", ""])
        assert completed["status"] == "completed"
        feedback = client.get(f"/api/sessions/{session['id']}/feedback").json()
        assert feedback["answered_questions"] == 0
        assert feedback["total_words"] == 0
        assert all(item["status"] == "not_enough_evidence" for item in feedback["question_feedback"])
        assert all(item["evidence"] is None for item in feedback["question_feedback"])
    finally:
        client.__exit__(None, None, None)


def test_cancellation_blocks_more_answers(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        session = client.post("/api/sessions").json()
        cancelled = client.post(f"/api/sessions/{session['id']}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        answer = client.post(
            f"/api/sessions/{session['id']}/answers",
            json={"question_id": "project_overview", "answer_text": "Cannot submit now."},
        )
        assert answer.status_code == 409
        retry = client.post(f"/api/sessions/{session['id']}/retry")
        assert retry.status_code == 409
    finally:
        client.__exit__(None, None, None)


def test_answer_length_is_bounded(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        session = client.post("/api/sessions").json()
        response = client.post(
            f"/api/sessions/{session['id']}/answers",
            json={"question_id": "project_overview", "answer_text": "x" * 6001},
        )
        assert response.status_code == 422
    finally:
        client.__exit__(None, None, None)


def test_legacy_database_is_migrated_without_dropping_sessions(tmp_path: Path) -> None:
    from prepped.database import initialize_database

    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                scenario_version TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'cancelled')),
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE TABLE answers (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                question_id TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                position INTEGER NOT NULL CHECK (position >= 0),
                created_at TEXT NOT NULL,
                UNIQUE (session_id, position)
            );
            INSERT INTO sessions (id, scenario_id, scenario_version, status, created_at)
            VALUES ('old-session', 'project-explanation', '1.0.0', 'completed', '2026-01-01T00:00:00+00:00');
            """
        )
    initialize_database(db_path)
    with sqlite3.connect(db_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(sessions)")}
        row = connection.execute(
            "SELECT attempt_group_id, attempt_number FROM sessions WHERE id='old-session'"
        ).fetchone()
    assert {"scenario_json", "rubric_json", "attempt_group_id", "attempt_number"}.issubset(columns)
    assert row == ("old-session", 1)


def test_scenario_loader_still_validates_duplicate_question_ids(tmp_path: Path) -> None:
    scenario = {
        "id": "bad", "version": "1", "title": "Bad scenario",
        "description": "Invalid fixture", "role": "Interviewer",
        "questions": [{"id": "same", "prompt": "First?"}, {"id": "same", "prompt": "Second?"}],
        "rubric": [{"id": "clarity", "label": "Clarity", "question": "Is it clear?"}],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(scenario), encoding="utf-8")
    try:
        load_scenario(path)
    except ValueError as exc:
        assert "Duplicate question id" in str(exc)
    else:
        raise AssertionError("Invalid scenario was accepted")
