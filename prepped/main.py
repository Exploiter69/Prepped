"""FastAPI entry point for the Prepped local practice application."""
from __future__ import annotations

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from prepped.database import connect_database, initialize_database
from prepped.feedback import build_feedback
from prepped.scenarios import DEFAULT_SCENARIO_PATH, ScenarioValidationError, load_scenario


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "prepped.sqlite3"
INDEX_PATH = ROOT / "static" / "index.html"
SCENARIO_ID = "project-explanation"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AnswerSubmission(BaseModel):
    question_id: str = Field(min_length=1, max_length=120)
    answer_text: str = Field(max_length=6000)


def _session_from_row(row: sqlite3.Row) -> dict[str, Any]:
    session = dict(row)
    try:
        session["scenario"] = json.loads(session.pop("scenario_json"))
        session["rubric"] = json.loads(session.pop("rubric_json"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Saved session configuration is unreadable.") from exc
    return session


def _get_session(connection: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Practice session not found.")
    return _session_from_row(row)


def _get_answers(connection: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT id, session_id, question_id, answer_text, position, created_at "
        "FROM answers WHERE session_id = ? ORDER BY position",
        (session_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _session_view(session: dict[str, Any], answers: list[dict[str, Any]]) -> dict[str, Any]:
    questions = session["scenario"].get("questions", [])
    answered_ids = {answer["question_id"] for answer in answers}
    next_question = next((q for q in questions if q["id"] not in answered_ids), None)
    return {
        "id": session["id"],
        "scenario_id": session["scenario_id"],
        "scenario_version": session["scenario_version"],
        "scenario_title": session["scenario"].get("title", "Practice session"),
        "status": session["status"],
        "created_at": session["created_at"],
        "completed_at": session["completed_at"],
        "attempt_group_id": session["attempt_group_id"],
        "attempt_number": session["attempt_number"],
        "question_count": len(questions),
        "answered_count": len(answers),
        "current_question": next_question,
        "answers": answers,
    }


def create_app(
    db_path: Path = DEFAULT_DB_PATH,
    scenario_path: Path = DEFAULT_SCENARIO_PATH,
) -> FastAPI:
    """Build an app with injectable local paths for isolated tests."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(Path(db_path))
        yield

    application = FastAPI(
        title="Prepped",
        description="A local-first scenario practice prototype.",
        version="0.2.0",
        lifespan=lifespan,
    )
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @application.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(INDEX_PATH)

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "application": "Prepped"}

    @application.get("/api/scenarios/project-explanation")
    def project_explanation_scenario() -> dict[str, Any]:
        try:
            return load_scenario(Path(scenario_path))
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=500, detail=f"Scenario configuration error: {exc}") from exc

    @application.post("/api/sessions", status_code=201)
    def start_session() -> dict[str, Any]:
        try:
            scenario = load_scenario(Path(scenario_path))
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=500, detail=f"Scenario configuration error: {exc}") from exc

        session_id = str(uuid4())
        created_at = _now()
        with connect_database(Path(db_path)) as connection:
            connection.execute(
                """
                INSERT INTO sessions
                    (id, scenario_id, scenario_version, status, created_at, completed_at,
                     scenario_json, rubric_json, attempt_group_id, attempt_number)
                VALUES (?, ?, ?, 'in_progress', ?, NULL, ?, ?, ?, 1)
                """,
                (
                    session_id, scenario["id"], scenario["version"], created_at,
                    json.dumps(scenario, ensure_ascii=False),
                    json.dumps(scenario["rubric"], ensure_ascii=False),
                    session_id,
                ),
            )
            session = _get_session(connection, session_id)
            return _session_view(session, [])

    @application.get("/api/sessions")
    def list_sessions() -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            rows = connection.execute(
                """
                SELECT id, scenario_id, scenario_version, status, created_at, completed_at,
                       attempt_group_id, attempt_number
                FROM sessions ORDER BY created_at DESC LIMIT 100
                """
            ).fetchall()
        return {"sessions": [dict(row) for row in rows]}

    @application.get("/api/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            session = _get_session(connection, session_id)
            answers = _get_answers(connection, session_id)
            return _session_view(session, answers)

    @application.post("/api/sessions/{session_id}/answers")
    def submit_answer(session_id: str, submission: AnswerSubmission) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            session = _get_session(connection, session_id)
            if session["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="This session is not accepting answers.")

            answers = _get_answers(connection, session_id)
            questions = session["scenario"].get("questions", [])
            if len(answers) >= len(questions):
                raise HTTPException(status_code=409, detail="All questions have already been answered.")

            expected_question = questions[len(answers)]
            if submission.question_id != expected_question["id"]:
                raise HTTPException(
                    status_code=409,
                    detail="Answer the current question before moving to the next one.",
                )

            connection.execute(
                """
                INSERT INTO answers (id, session_id, question_id, answer_text, position, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()), session_id, submission.question_id,
                    submission.answer_text.strip(), len(answers), _now(),
                ),
            )
            updated_answers = _get_answers(connection, session_id)
            completed_at = None
            if len(updated_answers) == len(questions):
                completed_at = _now()
                connection.execute(
                    "UPDATE sessions SET status = 'completed', completed_at = ? WHERE id = ?",
                    (completed_at, session_id),
                )
                session = _get_session(connection, session_id)
            return _session_view(session, updated_answers)

    @application.post("/api/sessions/{session_id}/cancel")
    def cancel_session(session_id: str) -> dict[str, str]:
        with connect_database(Path(db_path)) as connection:
            session = _get_session(connection, session_id)
            if session["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="Only an in-progress session can be cancelled.")
            connection.execute(
                "UPDATE sessions SET status = 'cancelled' WHERE id = ?",
                (session_id,),
            )
        return {"id": session_id, "status": "cancelled"}

    @application.get("/api/sessions/{session_id}/feedback")
    def session_feedback(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            session = _get_session(connection, session_id)
            if session["status"] != "completed":
                raise HTTPException(status_code=409, detail="Finish all questions before viewing feedback.")
            answers = _get_answers(connection, session_id)
            return build_feedback(session, answers)

    @application.post("/api/sessions/{session_id}/retry", status_code=201)
    def retry_session(session_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as connection:
            previous = _get_session(connection, session_id)
            if previous["status"] != "completed":
                raise HTTPException(status_code=409, detail="Complete this session before starting a retry.")
            next_attempt = connection.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) + 1 AS next_attempt "
                "FROM sessions WHERE attempt_group_id = ?",
                (previous["attempt_group_id"],),
            ).fetchone()["next_attempt"]
            new_id = str(uuid4())
            created_at = _now()
            connection.execute(
                """
                INSERT INTO sessions
                    (id, scenario_id, scenario_version, status, created_at, completed_at,
                     scenario_json, rubric_json, attempt_group_id, attempt_number)
                VALUES (?, ?, ?, 'in_progress', ?, NULL, ?, ?, ?, ?)
                """,
                (
                    new_id, previous["scenario_id"], previous["scenario_version"], created_at,
                    json.dumps(previous["scenario"], ensure_ascii=False),
                    json.dumps(previous["rubric"], ensure_ascii=False),
                    previous["attempt_group_id"], next_attempt,
                ),
            )
            session = _get_session(connection, new_id)
            return _session_view(session, [])

    @application.delete("/api/sessions/{session_id}", status_code=204)
    def delete_session(session_id: str) -> None:
        with connect_database(Path(db_path)) as connection:
            cursor = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Practice session not found.")
        return None

    return application


app = create_app()
