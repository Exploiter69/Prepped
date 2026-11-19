"""Versioned local curriculum and deterministic lesson runner."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database

DEFAULT_CURRICULUM_PATH = Path(__file__).resolve().parent.parent / "curriculum" / "curriculum.v1.json"
EXERCISE_TYPES = {"choice", "ordering", "reflection", "short_response", "vocabulary", "listening", "pronunciation"}


class CurriculumValidationError(ValueError):
    """Invalid or inconsistent versioned curriculum content."""


class StartAttempt(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=100)


class SubmitResponse(BaseModel):
    exercise_id: str = Field(min_length=1, max_length=100)
    answer: str | list[str]

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 6000:
                raise ValueError("Response must be 6,000 characters or fewer.")
            return value
        if len(value) > 40 or any(not isinstance(item, str) or len(item) > 100 for item in value):
            raise ValueError("Ordering response contains invalid items.")
        return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def load_curriculum(path: Path = DEFAULT_CURRICULUM_PATH) -> dict[str, Any]:
    """Read and validate the complete curriculum and all cross-references."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurriculumValidationError(f"Cannot read curriculum JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.1.0":
        raise CurriculumValidationError("Unsupported or missing curriculum schema_version.")
    arrays = [data.get(name) for name in ("skills", "tracks", "lessons", "levels", "units")]
    if not all(isinstance(items, list) for items in arrays):
        raise CurriculumValidationError("Curriculum must define skills, tracks, lessons, levels, and units arrays.")

    def index_items(items: list[dict], label: str) -> dict[str, dict]:
        index: dict[str, dict] = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                raise CurriculumValidationError(f"Every {label} must have a non-empty id.")
            if item["id"] in index:
                raise CurriculumValidationError(f"Duplicate {label} id: {item['id']}.")
            index[item["id"]] = item
        return index

    skills, tracks, lessons, levels, units = (
        index_items(items, name) for items, name in zip(arrays, ("skill", "track", "lesson", "level", "unit"))
    )
    if any(not item.get("title") or not item.get("description") for item in levels.values()):
        raise CurriculumValidationError("Every curriculum level needs a title and description.")
    for skill in skills.values():
        if skill.get("status", "active") not in {"active", "planned"} or not skill.get("title") or not skill.get("description") or not skill.get("outcomes"):
            raise CurriculumValidationError(f"Skill {skill['id']} has incomplete metadata.")
        if any(item not in skills or item == skill["id"] for item in skill.get("prerequisites", [])):
            raise CurriculumValidationError(f"Skill {skill['id']} has an invalid prerequisite.")
    for lesson in lessons.values():
        if (not all(lesson.get(key) for key in ("version", "title", "introduction"))
                or lesson.get("kind", "lesson") not in {"lesson", "diagnostic"}):
            raise CurriculumValidationError(f"Lesson {lesson['id']} is missing required metadata.")
        if lesson.get("kind", "lesson") == "lesson":
            example = lesson.get("example")
            if not isinstance(example, dict) or any(
                not isinstance(example.get(key), str) or not example[key].strip()
                for key in ("label", "before", "after", "explanation")
            ):
                raise CurriculumValidationError(f"Lesson {lesson['id']} needs a complete worked example.")
        if (lesson.get("track_id") not in tracks or lesson.get("level_id") not in levels
                or lesson.get("unit_id") not in units or not lesson.get("exercises")
                or not isinstance(lesson.get("estimated_minutes"), int) or lesson["estimated_minutes"] < 1
                or not lesson.get("learning_outcomes")):
            raise CurriculumValidationError(f"Lesson {lesson['id']} has invalid metadata or references.")
        if any(skill not in skills for skill in lesson.get("skill_ids", [])):
            raise CurriculumValidationError(f"Lesson {lesson['id']} references an unknown skill.")
        if any(prereq not in lessons or prereq == lesson["id"] for prereq in lesson.get("prerequisites", [])):
            raise CurriculumValidationError(f"Lesson {lesson['id']} has an invalid prerequisite.")
        seen: set[str] = set()
        for exercise in lesson["exercises"]:
            if not isinstance(exercise, dict):
                raise CurriculumValidationError(f"Lesson {lesson['id']} contains an invalid exercise object.")
            eid, kind = exercise.get("id"), exercise.get("type")
            if not exercise.get("prompt") or not eid or eid in seen or kind not in EXERCISE_TYPES:
                raise CurriculumValidationError(f"Lesson {lesson['id']} has an invalid exercise.")
            seen.add(eid)
            if kind in {"choice", "vocabulary", "listening"}:
                ids = [option.get("id") for option in exercise.get("options", [])]
                if len(ids) < 2 or len(ids) != len(set(ids)) or exercise.get("answer") not in ids:
                    raise CurriculumValidationError(f"Choice exercise {eid} has invalid options or answer.")
                if kind == "vocabulary" and not exercise.get("context"):
                    raise CurriculumValidationError(f"Vocabulary exercise {eid} needs a context.")
                if kind == "listening" and (not exercise.get("audio_text") or not exercise.get("transcript")):
                    raise CurriculumValidationError(f"Listening exercise {eid} needs playable audio and a text alternative.")
            elif kind == "pronunciation":
                if not exercise.get("audio_text") or not exercise.get("transcript") or not exercise.get("guidance"):
                    raise CurriculumValidationError(f"Pronunciation exercise {eid} needs playable audio, a text alternative, and self-review guidance.")
            elif kind == "ordering":
                ids, answer = [token.get("id") for token in exercise.get("tokens", [])], exercise.get("answer")
                if len(ids) < 2 or len(ids) != len(set(ids)) or not isinstance(answer, list) or sorted(answer) != sorted(ids):
                    raise CurriculumValidationError(f"Ordering exercise {eid} has invalid tokens or answer.")
            elif not exercise.get("guidance"):
                raise CurriculumValidationError(f"Reflection exercise {eid} needs self-review guidance.")
    def reject_cycles(graph: dict[str, list[str]], label: str) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise CurriculumValidationError(f"{label} prerequisite cycle includes {node}.")
            if node in visited:
                return
            visiting.add(node)
            for parent in graph.get(node, []):
                visit(parent)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)
    reject_cycles({key: item.get("prerequisites", []) for key, item in skills.items()}, "Skill")
    reject_cycles({key: item.get("prerequisites", []) for key, item in lessons.items()}, "Lesson")

    for unit in units.values():
        if (unit.get("level_id") not in levels or not unit.get("title") or not unit.get("description")
                or not unit.get("track_ids") or not unit.get("lesson_ids")
                or not isinstance(unit.get("learning_outcomes"), list) or not unit["learning_outcomes"]
                or any(not isinstance(outcome, str) or not outcome.strip() for outcome in unit["learning_outcomes"])):
            raise CurriculumValidationError(f"Unit {unit['id']} has incomplete level, track, or lesson references.")
        if len(unit["track_ids"]) != len(set(unit["track_ids"])) or any(track_id not in tracks for track_id in unit["track_ids"]):
            raise CurriculumValidationError(f"Unit {unit['id']} references an unknown track.")
        if len(unit["lesson_ids"]) != len(set(unit["lesson_ids"])) or any(
            lesson_id not in lessons or lessons[lesson_id].get("unit_id") != unit["id"]
            or lessons[lesson_id].get("track_id") not in unit["track_ids"]
            for lesson_id in unit["lesson_ids"]
        ):
            raise CurriculumValidationError(f"Unit {unit['id']} has an invalid lesson reference.")

    valid_goals = {"english_fluency", "placement_interviews", "technical_interviews", "project_communication", "professional_communication"}
    for track in tracks.values():
        if track.get("level_id") not in levels or not track.get("title") or not track.get("description") or not track.get("unit_ids"):
            raise CurriculumValidationError(f"Track {track['id']} has an invalid level or no units.")
        if len(track["unit_ids"]) != len(set(track["unit_ids"])) or any(
            unit_id not in units or track["id"] not in units[unit_id]["track_ids"]
            or units[unit_id]["level_id"] != track["level_id"]
            for unit_id in track["unit_ids"]
        ):
            raise CurriculumValidationError(f"Track {track['id']} has an invalid unit reference.")
        if track.get("goal") not in valid_goals:
            raise CurriculumValidationError(f"Track {track['id']} has an unsupported goal.")
        if (len(track.get("lesson_ids", [])) != len(set(track.get("lesson_ids", [])))
                or any(lesson_id not in lessons for lesson_id in track.get("lesson_ids", []))):
            raise CurriculumValidationError(f"Track {track['id']} has an invalid lesson reference.")
        if any(skill_id not in skills for skill_id in track.get("skill_ids", [])):
            raise CurriculumValidationError(f"Track {track['id']} references an unknown skill.")
    return data


def _public_exercise(exercise: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in exercise.items() if key not in {"answer", "explanation"}}


def _public_lesson(lesson: dict[str, Any]) -> dict[str, Any]:
    return {**{key: value for key, value in lesson.items() if key != "exercises"},
            "exercises": [_public_exercise(item) for item in lesson["exercises"]],
            "exercise_count": len(lesson["exercises"])}


def _profile(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM learner_profile WHERE id = 1").fetchone()
    if row is None:
        return None
    result = dict(row)
    try:
        result["improvement_areas"] = json.loads(result.pop("improvement_areas_json"))
    except (TypeError, json.JSONDecodeError):
        result["improvement_areas"] = []
    return result


def build_recommendations(curriculum: dict[str, Any], profile: dict[str, Any] | None) -> dict[str, Any]:
    """Select a transparent starter route from declared preferences, never inferred ability."""
    goal = profile.get("primary_goal") if profile else "placement_interviews"
    track_id = {
        "english_fluency": "english-foundations",
        "placement_interviews": "placement-communication",
        "technical_interviews": "placement-communication",
        "project_communication": "project-communication",
        "professional_communication": "project-communication",
    }.get(goal, "placement-communication")
    track = next(item for item in curriculum["tracks"] if item["id"] == track_id)
    lessons = {item["id"]: item for item in curriculum["lessons"]}
    areas = set(profile.get("improvement_areas", [])) if profile else set()
    items = []
    covered_areas: set[str] = set()
    for lesson_id in track["lesson_ids"]:
        lesson = lessons[lesson_id]
        matched = []
        if "grammar" in areas and "english.grammar-in-context" in lesson["skill_ids"]:
            matched.append("grammar")
            covered_areas.add("grammar")
        if "vocabulary" in areas and "english.vocabulary-context" in lesson["skill_ids"]:
            matched.append("vocabulary")
            covered_areas.add("vocabulary")
        if "speaking_fluency" in areas and "english.fluency" in lesson["skill_ids"]:
            matched.append("speaking fluency practice")
            covered_areas.add("speaking_fluency")
        if "pronunciation" in areas and "english.pronunciation" in lesson["skill_ids"]:
            matched.append("listen-and-repeat pronunciation practice")
            covered_areas.add("pronunciation")
        if "confidence" in areas and "communication.confidence" in lesson["skill_ids"]:
            matched.append("low-pressure speaking practice")
            covered_areas.add("confidence")
        if "project_explanation" in areas and "communication.project-summary" in lesson["skill_ids"]:
            matched.append("project explanation")
            covered_areas.add("project_explanation")
        if "professional_communication" in areas and (
                "communication.clarity" in lesson["skill_ids"] or "communication.professional" in lesson["skill_ids"]):
            matched.append("professional communication")
            covered_areas.add("professional_communication")
        why = ("Matches your focus on " + ", ".join(matched) + ".") if matched else (
            f"Included in the {track['title']} path selected for your {goal.replace('_', ' ')} goal."
        )
        items.append({"lesson_id": lesson_id, "title": lesson["title"], "summary": lesson["summary"],
                      "estimated_minutes": lesson["estimated_minutes"], "skill_ids": lesson["skill_ids"], "why": why})
    missing = sorted(areas - covered_areas)
    if goal == "technical_interviews":
        note = "A dedicated technical-interview question bank is planned. This route builds project-explanation foundations first."
    elif missing:
        note = "These selected focus areas do not yet have dedicated lessons: " + ", ".join(missing) + "."
    else:
        note = "This starter route follows your saved goal and focus areas. You can choose any available lesson."
    return {"profile_configured": profile is not None, "goal": goal, "track_id": track_id,
            "track_title": track["title"], "track_description": track["description"], "items": items, "note": note}


def _feedback(exercise: dict[str, Any], answer: str | list[str], example_to_compare: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"exercise_id": exercise["id"], "type": exercise["type"], "prompt": exercise["prompt"]}
    if exercise["type"] in {"choice", "vocabulary", "listening"}:
        selected = answer if isinstance(answer, str) else ""
        option = next((item for item in exercise["options"] if item["id"] == selected), None)
        correct = next(item for item in exercise["options"] if item["id"] == exercise["answer"])
        result.update({"status": "correct" if selected == exercise["answer"] else "review",
                       "selected": option["label"] if option else "No valid option selected",
                       "correct_answer": correct["label"], "explanation": exercise["explanation"]})
    elif exercise["type"] == "ordering":
        selected = answer if isinstance(answer, list) else []
        labels = {item["id"]: item["label"] for item in exercise["tokens"]}
        result.update({"status": "correct" if selected == exercise["answer"] else "review",
                       "your_order": [labels[item] for item in selected if item in labels],
                       "suggested_order": [labels[item] for item in exercise["answer"]],
                       "explanation": exercise["explanation"]})
    else:
        text = answer if isinstance(answer, str) else ""
        if exercise["type"] == "pronunciation" and not text:
            text = "Practice completed privately; no transcript or note was saved."
        result.update({"status": "saved_for_self_review", "original_response": text,
                       "guidance": exercise["guidance"],
                       "example_to_compare": example_to_compare,
                       "example_note": "An illustrative example only; it is not an automated correction or grade.",
                       "note": "This open response is saved as your work. Prepped does not automatically grade it."})
        if exercise["type"] == "pronunciation":
            result["measurement_note"] = (
                "Listen-and-repeat practice only. Prepped does not measure pronunciation, accent, "
                "phoneme accuracy, or speaking fluency."
            )
    return result


def create_learning_router(db_path: Path, curriculum_path: Path = DEFAULT_CURRICULUM_PATH) -> APIRouter:
    router = APIRouter(prefix="/api/learning", tags=["learning"])

    def curriculum_data() -> dict[str, Any]:
        try:
            return load_curriculum(Path(curriculum_path))
        except CurriculumValidationError as exc:
            raise HTTPException(status_code=500, detail=f"Curriculum configuration error: {exc}") from exc

    def get_attempt(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any]:
        row = connection.execute("SELECT * FROM learning_attempts WHERE id = ?", (attempt_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Learning attempt not found.")
        item = dict(row)
        item["responses"] = json.loads(item.pop("responses_json"))
        item["lesson_snapshot"] = json.loads(item.pop("lesson_json") or "{}")
        item["feedback"] = json.loads(item.pop("feedback_json")) if item["feedback_json"] else []
        item.pop("feedback_json", None)
        return item

    def view(attempt: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        lesson = attempt.get("lesson_snapshot") or next((item for item in data["lessons"] if item["id"] == attempt["lesson_id"]), None)
        if lesson is None:
            raise HTTPException(status_code=410, detail="This lesson is no longer in the installed curriculum.")
        index = len(attempt["responses"])
        current = lesson["exercises"][index] if attempt["status"] == "in_progress" and index < len(lesson["exercises"]) else None
        track = next((item for item in data["tracks"] if item["id"] == lesson["track_id"]), None)
        ordered_lessons = track.get("lesson_ids", []) if track else []
        next_id = ordered_lessons[ordered_lessons.index(lesson["id"]) + 1] if lesson["id"] in ordered_lessons and ordered_lessons.index(lesson["id"]) + 1 < len(ordered_lessons) else None
        next_lesson = next(({"lesson_id": item["id"], "title": item["title"]}
                            for item in data["lessons"] if item["id"] == next_id), None)
        return {"id": attempt["id"], "lesson_id": attempt["lesson_id"], "lesson_version": attempt["lesson_version"],
                "track_id": attempt["track_id"], "status": attempt["status"], "started_at": attempt["started_at"],
                "completed_at": attempt["completed_at"], "response_count": len(attempt["responses"]),
                "exercise_count": len(lesson["exercises"]), "lesson": _public_lesson(lesson),
                "current_exercise": _public_exercise(current) if current else None,
                "next_lesson": next_lesson, "feedback": attempt["feedback"]}

    @router.get("/catalog")
    def catalog() -> dict[str, Any]:
        data = curriculum_data()
        with connect_database(Path(db_path)) as conn:
            profile = _profile(conn)
        return {"schema_version": data["schema_version"], "levels": data["levels"],
                "units": data["units"], "skills": data["skills"],
                "tracks": [{**{k: v for k, v in track.items() if k != "lesson_ids"},
                            "lessons": [_public_lesson(next(x for x in data["lessons"] if x["id"] == lid))
                                        for lid in track["lesson_ids"]]} for track in data["tracks"]],
                "recommendations": build_recommendations(data, profile)}

    @router.get("/recommendations")
    def recommendations() -> dict[str, Any]:
        data = curriculum_data()
        with connect_database(Path(db_path)) as conn:
            profile = _profile(conn)
        return build_recommendations(data, profile)

    @router.post("/attempts", status_code=201)
    def start_attempt(payload: StartAttempt) -> dict[str, Any]:
        data = curriculum_data()
        lesson = next((item for item in data["lessons"] if item["id"] == payload.lesson_id), None)
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        with connect_database(Path(db_path)) as conn:
            # Lesson prerequisites guide the recommended order; they never block learner access.
            attempt_id, started = str(uuid4()), _now()
            conn.execute("""INSERT INTO learning_attempts
                (id, lesson_id, lesson_version, track_id, lesson_json, status, responses_json, feedback_json, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, 'in_progress', '[]', NULL, ?, NULL)""",
                (attempt_id, lesson["id"], lesson["version"], lesson["track_id"],
                 json.dumps(lesson, ensure_ascii=False), started))
            conn.execute("""INSERT INTO learning_events
                (id, event_type, attempt_id, lesson_id, skill_ids_json, occurred_at, detail_json)
                VALUES (?, 'lesson_started', ?, ?, ?, ?, '{}')""",
                (str(uuid4()), attempt_id, lesson["id"], json.dumps(lesson["skill_ids"]), started))
            attempt = get_attempt(conn, attempt_id)
        return view(attempt, data)

    @router.get("/attempts/{attempt_id}")
    def read_attempt(attempt_id: str) -> dict[str, Any]:
        data = curriculum_data()
        with connect_database(Path(db_path)) as conn:
            attempt = get_attempt(conn, attempt_id)
        return view(attempt, data)

    @router.post("/attempts/{attempt_id}/responses")
    def submit_response(attempt_id: str, payload: SubmitResponse) -> dict[str, Any]:
        data = curriculum_data()
        with connect_database(Path(db_path)) as conn:
            attempt = get_attempt(conn, attempt_id)
            if attempt["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="This lesson attempt is already complete.")
            lesson = attempt.get("lesson_snapshot") or next((item for item in data["lessons"] if item["id"] == attempt["lesson_id"]), None)
            if lesson is None:
                raise HTTPException(status_code=410, detail="This lesson is no longer in the installed curriculum.")
            index = len(attempt["responses"])
            if index >= len(lesson["exercises"]):
                raise HTTPException(status_code=409, detail="All lesson exercises have already been answered.")
            exercise = lesson["exercises"][index]
            if payload.exercise_id != exercise["id"]:
                raise HTTPException(status_code=409, detail="Complete the current exercise before moving on.")
            if isinstance(payload.answer, str) and not payload.answer and exercise["type"] != "pronunciation":
                raise HTTPException(status_code=422, detail="Enter a response before continuing.")
            if exercise["type"] in {"choice", "vocabulary", "listening"}:
                valid = {item["id"] for item in exercise["options"]}
                if not isinstance(payload.answer, str) or payload.answer not in valid:
                    raise HTTPException(status_code=422, detail="Choose one of the available options.")
            elif exercise["type"] == "ordering":
                valid = {item["id"] for item in exercise["tokens"]}
                if not isinstance(payload.answer, list) or len(payload.answer) != len(valid) or set(payload.answer) != valid:
                    raise HTTPException(status_code=422, detail="Arrange every item exactly once.")
            elif not isinstance(payload.answer, str):
                raise HTTPException(status_code=422, detail="Enter a written response for this reflection.")
            responses = [*attempt["responses"], {"exercise_id": exercise["id"], "answer": payload.answer}]
            example = lesson.get("example", {}).get("after")
            feedback = [*attempt["feedback"], _feedback(exercise, payload.answer, example)]
            now = _now()
            conn.execute("UPDATE learning_attempts SET responses_json = ?, feedback_json = ? WHERE id = ?",
                         (json.dumps(responses, ensure_ascii=False), json.dumps(feedback, ensure_ascii=False), attempt_id))
            conn.execute("""INSERT INTO learning_events
                (id, event_type, attempt_id, lesson_id, skill_ids_json, occurred_at, detail_json)
                VALUES (?, 'response_submitted', ?, ?, ?, ?, ?)""",
                (str(uuid4()), attempt_id, lesson["id"], json.dumps(lesson["skill_ids"]), now,
                 json.dumps({"exercise_id": exercise["id"], "exercise_type": exercise["type"]})))
            if len(responses) == len(lesson["exercises"]):
                conn.execute("UPDATE learning_attempts SET status = 'completed', completed_at = ? WHERE id = ?",
                             (now, attempt_id))
                conn.execute("""INSERT INTO learning_events
                    (id, event_type, attempt_id, lesson_id, skill_ids_json, occurred_at, detail_json)
                    VALUES (?, 'lesson_completed', ?, ?, ?, ?, '{}')""",
                    (str(uuid4()), attempt_id, lesson["id"], json.dumps(lesson["skill_ids"]), now))
            updated = get_attempt(conn, attempt_id)
        return view(updated, data)

    @router.get("/diagnostic/latest")
    def latest_diagnostic() -> dict[str, Any]:
        data = curriculum_data()
        diagnostic = next((item for item in data["lessons"] if item.get("kind") == "diagnostic"), None)
        if diagnostic is None:
            return {"configured": False, "latest": None}
        with connect_database(Path(db_path)) as conn:
            rows = conn.execute(
                "SELECT id, status, started_at, completed_at FROM learning_attempts WHERE lesson_id = ? ORDER BY started_at DESC",
                (diagnostic["id"],),
            ).fetchall()
            if not rows:
                return {"configured": True, "latest": None, "history": [],
                        "note": "This is a low-stakes snapshot of responses, not a proficiency test."}
            attempt = get_attempt(conn, rows[0]["id"])
        return {"configured": True, "latest": view(attempt, data),
                "history": [dict(row) for row in rows],
                "note": "Responses are stored for later comparison. No proficiency level or overall score is assigned."}

    @router.get("/progress")
    def progress() -> dict[str, Any]:
        data = curriculum_data()
        with connect_database(Path(db_path)) as conn:
            rows = conn.execute("SELECT id, lesson_id, track_id, status, started_at, completed_at FROM learning_attempts ORDER BY started_at DESC").fetchall()
            event_count = conn.execute("SELECT COUNT(*) AS n FROM learning_events").fetchone()["n"]
        diagnostic_ids = {lesson["id"] for lesson in data["lessons"] if lesson.get("kind") == "diagnostic"}
        completed_by_lesson = {
            row["lesson_id"] for row in rows
            if row["status"] == "completed" and row["lesson_id"] not in diagnostic_ids
        }
        lesson_completions = sum(
            row["status"] == "completed" and row["lesson_id"] not in diagnostic_ids for row in rows
        )
        diagnostics_completed = sum(
            row["status"] == "completed" and row["lesson_id"] in diagnostic_ids for row in rows
        )
        diagnostic_attempts_started = sum(row["lesson_id"] in diagnostic_ids for row in rows)
        skills = []
        for skill in data["skills"]:
            lesson_ids = [lesson["id"] for lesson in data["lessons"] if skill["id"] in lesson["skill_ids"]]
            skills.append({"skill_id": skill["id"], "title": skill["title"],
                           "status": skill.get("status", "active"), "description": skill["description"],
                           "outcomes": skill.get("outcomes", []),
                           "completed_lessons": sum(item in completed_by_lesson for item in lesson_ids),
                           "available_lessons": len(lesson_ids)})
        return {"attempts_started": len(rows), "lessons_completed": len(completed_by_lesson),
                "lesson_completions": lesson_completions,
                "diagnostic_attempts_started": diagnostic_attempts_started,
                "diagnostics_completed": diagnostics_completed,
                "learning_events": event_count, "skills": skills,
                "completed_lesson_ids": sorted(completed_by_lesson),
                "active_attempts": [dict(row) for row in rows if row["status"] == "in_progress"],
                "recent_attempts": [dict(row) for row in rows[:10]],
                "note": "Counts show recorded activity only. They are not proficiency levels or a measure of learning gain."}

    return router
