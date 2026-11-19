"""FastAPI entry point for the Prepped local practice application."""
from __future__ import annotations

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from prepped.database import connect_database, initialize_database
from prepped.career import create_career_router, initialize_career_database
from prepped.feedback import build_feedback
from prepped.profile import create_profile_router
from prepped.learning import DEFAULT_CURRICULUM_PATH, create_learning_router, load_curriculum
from prepped.memory import create_memory_router
from prepped.progress import create_progress_router, initialize_progress_database
from prepped.portability import create_portability_router
from prepped.scenarios import DEFAULT_SCENARIO_PATH, ScenarioValidationError, load_scenario
from prepped.voice import VoiceService, build_voice_service
from prepped.voice.routes import create_voice_router


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
    voice_service: VoiceService | None = None,
    curriculum_path: Path = DEFAULT_CURRICULUM_PATH,
) -> FastAPI:
    """Build an app with injectable local paths and voice engines for tests."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(Path(db_path))
        initialize_career_database(Path(db_path))
        initialize_progress_database(Path(db_path))
        load_curriculum(Path(curriculum_path))
        yield

    application = FastAPI(
        title="Prepped",
        description="A local-first, voice-enabled scenario practice prototype.",
        version="0.3.0",
        lifespan=lifespan,
    )
    @application.middleware("http")
    async def local_security_headers(request, call_next):
        host_header = request.headers.get("host", "")
        hostname = urlsplit("//" + host_header).hostname
        if hostname not in {"127.0.0.1", "localhost", "::1", "testserver"}:
            return PlainTextResponse("Prepped accepts local connections only.", status_code=400)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin:
                parsed_origin = urlsplit(origin)
                if parsed_origin.scheme not in {"http", "https"} or parsed_origin.netloc.lower() != host_header.lower():
                    return PlainTextResponse("Cross-origin state changes are not allowed.", status_code=403)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    application.include_router(create_voice_router(voice_service or build_voice_service()))
    application.include_router(create_profile_router(Path(db_path)))
    application.include_router(create_learning_router(Path(db_path), Path(curriculum_path)))
    application.include_router(create_memory_router(Path(db_path)))
    application.include_router(create_progress_router(Path(db_path), Path(curriculum_path)))
    application.include_router(create_portability_router(Path(db_path)))
    application.include_router(create_career_router(Path(db_path)))

    @application.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(INDEX_PATH)

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "application": "Prepped"}

    @application.get("/api/ready")
    def readiness() -> dict[str, Any]:
        try:
            with connect_database(Path(db_path)) as connection:
                integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
                required = {"sessions", "answers", "learner_profile", "learning_attempts",
                            "learning_events", "learning_memory", "learning_memory_reviews",
                            "career_sessions", "career_turns", "learner_goals"}
                existing = {row["name"] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                if integrity != "ok" or not required.issubset(existing):
                    raise RuntimeError("Database check failed.")
            load_curriculum(Path(curriculum_path))
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Local data or curriculum is not ready. Check the local application files.") from exc
        return {"status": "ready", "application": "Prepped", "database": "ok", "curriculum": "ok"}

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
