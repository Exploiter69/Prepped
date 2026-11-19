"""Evidence-based progress summaries and learner-owned practice goals."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database
from prepped.learning import build_recommendations, load_curriculum

GoalType = Literal["lessons_completed", "practice_sessions", "interviews_completed", "memory_reviews"]
GOAL_TABLE = """
CREATE TABLE IF NOT EXISTS learner_goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 240),
    goal_type TEXT NOT NULL CHECK (goal_type IN ('lessons_completed','practice_sessions','interviews_completed','memory_reviews')),
    target_count INTEGER NOT NULL CHECK (target_count BETWEEN 1 AND 500),
    baseline_count INTEGER NOT NULL DEFAULT 0 CHECK (baseline_count >= 0),
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','archived')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learner_goals_status ON learner_goals(status, due_date);
"""

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds")

def initialize_progress_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as conn:
        conn.executescript(GOAL_TABLE)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(learner_goals)")}
        if "baseline_count" not in columns:
            conn.execute("ALTER TABLE learner_goals ADD COLUMN baseline_count INTEGER NOT NULL DEFAULT 0")
        conn.execute("PRAGMA user_version = 2")

class GoalPayload(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=240)
    goal_type: GoalType
    target_count: int = Field(ge=1, le=500)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Give your goal a short title.")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return value.strip()

def _activity_count(conn: sqlite3.Connection, goal_type: str) -> int:
    queries = {
        "lessons_completed": "SELECT COUNT(DISTINCT lesson_id) AS n FROM learning_attempts WHERE status='completed' AND lesson_id != 'baseline-check'",
        "practice_sessions": "SELECT COUNT(*) AS n FROM sessions WHERE status='completed'",
        "interviews_completed": "SELECT COUNT(*) AS n FROM career_sessions WHERE status='completed'",
        "memory_reviews": "SELECT COUNT(*) AS n FROM learning_memory_reviews",
    }
    row = conn.execute(queries[goal_type]).fetchone()
    return int(row["n"] or 0)

def _goal_progress(conn: sqlite3.Connection, goal_type: str, baseline_count: int) -> int:
    return max(0, _activity_count(conn, goal_type) - baseline_count)

def _goal_view(conn: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    progress = _goal_progress(conn, item["goal_type"], item["baseline_count"])
    item.update({"current_count": progress, "remaining": max(0, item["target_count"] - progress),
                 "reached_target": progress >= item["target_count"]})
    return item

def _profile(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM learner_profile WHERE id=1").fetchone()
    if row is None:
        return None
    result = dict(row)
    try:
        result["improvement_areas"] = json.loads(result.pop("improvement_areas_json"))
    except (TypeError, json.JSONDecodeError):
        result["improvement_areas"] = []
    return result

def _recent_activity(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in conn.execute("SELECT id, lesson_id, event_type, occurred_at FROM learning_events ORDER BY occurred_at DESC LIMIT 100"):
        if row["event_type"] == "lesson_completed":
            lesson = conn.execute("SELECT lesson_json FROM learning_attempts WHERE id=(SELECT attempt_id FROM learning_events WHERE id=?)", (row["id"],)).fetchone()
            title = row["lesson_id"].replace("-", " ").title()
            if lesson:
                try:
                    title = json.loads(lesson["lesson_json"]).get("title", title)
                except (TypeError, json.JSONDecodeError):
                    pass
            items.append({"id": row["id"], "type": "lesson", "title": "Completed: " + title, "occurred_at": row["occurred_at"]})
    for row in conn.execute("undefined ORDER BY COALESCE(completed_at, created_at) DESC LIMIT 100"):
        items.append({"id": row["id"], "type": "practice", "title": "Project practice " + ("completed" if row["status"] == "completed" else "started"), "occurred_at": row["completed_at"] or row["created_at"]})
    names = {"project-explanation": "Project explanation", "hr-behavioural": "HR & behavioural", "technical-fundamentals": "Technical fundamentals"}
    for row in conn.execute("SELECT id, studio_id, status, created_at, completed_at FROM career_sessions ORDER BY COALESCE(completed_at, created_at) DESC LIMIT 100"):
        items.append({"id": row["id"], "type": "interview", "title": names.get(row["studio_id"], row["studio_id"]) + " interview " + ("completed" if row["status"] == "completed" else "started"), "occurred_at": row["completed_at"] or row["created_at"]})
    for row in conn.execute("SELECT id, rating, reviewed_at FROM learning_memory_reviews ORDER BY reviewed_at DESC LIMIT 100"):
        items.append({"id": row["id"], "type": "review", "title": "Learning memory reviewed · " + row["rating"].title(), "occurred_at": row["reviewed_at"]})
    items.sort(key=lambda item: item["occurred_at"] or "", reverse=True)
    return items[:limit]

def _overview(db_path: Path, curriculum_path: Path) -> dict[str, Any]:
    curriculum = load_curriculum(Path(curriculum_path))
    now = _now()
    start = (now.date() - timedelta(days=6)).isoformat()
    with connect_database(Path(db_path)) as conn:
        profile = _profile(conn)
        lesson_rows = conn.execute("SELECT id, lesson_id, status, lesson_json, started_at, completed_at FROM learning_attempts ORDER BY started_at DESC, rowid DESC").fetchall()
        events = conn.execute("SELECT lesson_id, skill_ids_json, occurred_at FROM learning_events WHERE event_type='lesson_completed' ORDER BY occurred_at DESC").fetchall()
        practice = conn.execute("SELECT id, status, created_at, completed_at FROM sessions ORDER BY COALESCE(completed_at,created_at) DESC, rowid DESC").fetchall()
        interviews = conn.execute("SELECT status, created_at, completed_at, studio_id FROM career_sessions ORDER BY COALESCE(completed_at,created_at) DESC, rowid DESC").fetchall()
        memory = conn.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='active' AND dismissed_at IS NULL AND due_at<=? THEN 1 ELSE 0 END) AS due FROM learning_memory", (_stamp(now),)).fetchone()
        review_total = int(conn.execute("SELECT COUNT(*) AS n FROM learning_memory_reviews").fetchone()["n"] or 0)
        review_rows = conn.execute("SELECT reviewed_at FROM learning_memory_reviews WHERE reviewed_at >= ?", (start,)).fetchall()
        active_goals = [_goal_view(conn, row) for row in conn.execute("SELECT * FROM learner_goals WHERE status='active' ORDER BY COALESCE(due_date,'9999-12-31'), created_at")]
        goals_total = int(conn.execute("SELECT COUNT(*) AS n FROM learner_goals").fetchone()["n"] or 0)
        diagnostic_ids = {lesson["id"] for lesson in curriculum["lessons"] if lesson.get("kind") == "diagnostic"}
        completed_ids = {row["lesson_id"] for row in lesson_rows if row["status"] == "completed" and row["lesson_id"] not in diagnostic_ids}
        skill_evidence: dict[str, set[str]] = {skill["id"]: set() for skill in curriculum["skills"]}
        for event in events:
            if event["lesson_id"] in diagnostic_ids:
                continue
            try:
                skill_ids = json.loads(event["skill_ids_json"])
            except (TypeError, json.JSONDecodeError):
                skill_ids = []
            for skill_id in skill_ids:
                if skill_id in skill_evidence:
                    skill_evidence[skill_id].add(event["lesson_id"])
        lessons = {lesson["id"]: lesson for lesson in curriculum["lessons"]}
        skills = []
        for skill in curriculum["skills"]:
            linked = [lesson for lesson in curriculum["lessons"]
                      if lesson.get("kind") != "diagnostic" and skill["id"] in lesson["skill_ids"]]
            done = sorted(skill_evidence[skill["id"]])
            skills.append({
                "skill_id": skill["id"], "title": skill["title"], "category": skill.get("category", "general"),
                "description": skill["description"], "completed_lessons": len(done),
                "available_lessons": len(linked), "started_lessons": len({row["lesson_id"] for row in lesson_rows if row["lesson_id"] in {lesson["id"] for lesson in linked}}),
                "completion_percent": round(100 * len(done) / len(linked)) if linked else 0,
                "evidence": [{"lesson_id": lesson_id, "title": lessons.get(lesson_id, {}).get("title", lesson_id)} for lesson_id in done],
                "note": "Completed lesson links only; this is activity evidence, not a proficiency rating."
            })
        lesson_count = len(completed_ids)
        practice_completed = sum(row["status"] == "completed" for row in practice)
        interviews_completed = sum(row["status"] == "completed" for row in interviews)
        weekly = { (now.date() - timedelta(days=offset)).isoformat(): 0 for offset in range(6, -1, -1) }
        for row in events:
            day = (row["occurred_at"] or "")[:10]
            if day in weekly and row["lesson_id"] in completed_ids:
                weekly[day] += 1
        for row in practice:
            day = (row["completed_at"] or "")[:10]
            if row["status"] == "completed" and day in weekly:
                weekly[day] += 1
        for row in interviews:
            day = (row["completed_at"] or "")[:10]
            if row["status"] == "completed" and day in weekly:
                weekly[day] += 1
        for row in review_rows:
            day = (row["reviewed_at"] or "")[:10]
            if day in weekly:
                weekly[day] += 1
        activity = _recent_activity(conn)
        recommendations = []
        in_progress = next((row for row in lesson_rows if row["status"] == "in_progress"), None)
        if in_progress:
            recommendations.append({"kind": "resume_lesson", "title": "Resume your lesson", "reason": "You have a saved lesson attempt that has not been completed.", "target_id": in_progress["id"]})
        in_progress_practice = next((row for row in practice if row["status"] == "in_progress"), None)
        if in_progress_practice:
            recommendations.append({"kind": "resume_practice", "title": "Resume project practice", "reason": "You have a saved project-practice session with unanswered prompts.", "target_id": in_progress_practice["id"]})
        in_progress_interview = next((row for row in interviews if row["status"] == "in_progress"), None)
        if in_progress_interview:
            studio_title = {"project-explanation": "Project explanation", "hr-behavioural": "HR & behavioural", "technical-fundamentals": "Technical fundamentals"}.get(in_progress_interview["studio_id"], "Career")
            recommendations.append({"kind": "resume_interview", "title": "Resume: " + studio_title, "reason": "You have a saved interview with unanswered turns.", "target_id": in_progress_interview["id"]})
        due = int(memory["due"] or 0)
        if due:
            recommendations.append({"kind": "review_memory", "title": f"Review {due} due learning note(s)", "reason": "These learner-saved notes have reached their next review date.", "target_id": "learning-memory"})
        route = build_recommendations(curriculum, profile)
        active_lesson_id = in_progress["lesson_id"] if in_progress else None
        next_lesson = next((item for item in route["items"]
                            if item["lesson_id"] not in completed_ids and item["lesson_id"] != active_lesson_id), None)
        if next_lesson:
            recommendations.append({"kind": "lesson", "title": "Continue: " + next_lesson["title"], "reason": next_lesson["why"], "target_id": next_lesson["lesson_id"]})
        if active_goals:
            goal = active_goals[0]
            recommendations.append({"kind": "goal", "title": "Work toward: " + goal["title"], "reason": f"{goal['current_count']} of {goal['target_count']} {goal['goal_type'].replace('_',' ')} recorded.", "target_id": goal["id"]})
        if not recommendations:
            recommendations.append({"kind": "choose_goal", "title": "Choose a small practice goal", "reason": "A short, learner-chosen target makes the next action clear without estimating ability.", "target_id": "goals"})
        return {
            "generated_at": _stamp(now),
            "summary": {"lessons_completed": lesson_count, "practice_sessions_completed": practice_completed,
                        "interviews_completed": interviews_completed, "memory_reviews_completed": review_total,
                        "due_memory_items": due, "active_goals": len(active_goals), "goals_total": goals_total,
                        "lesson_attempts_started": len(lesson_rows), "practice_sessions_started": len(practice),
                        "interviews_started": len(interviews)},
            "skills": skills,
            "weekly_activity": [{"date": day, "count": count} for day, count in weekly.items()],
            "goals": active_goals,
            "recent_activity": activity,
            "recommendations": recommendations,
            "profile_goal": profile["primary_goal"] if profile else None,
            "notes": ["Counts reflect saved activity only; they are not proficiency levels, confidence measurements, learning gains, or placement predictions.",
                      "Skill evidence is linked to completed curriculum lessons. Project practice, interview completion, and memory review are shown separately."]
        }

def create_progress_router(db_path: Path, curriculum_path: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/api/progress/overview")
    def overview() -> dict[str, Any]:
        return _overview(Path(db_path), Path(curriculum_path))

    @router.get("/api/goals")
    def list_goals(include_archived: bool = False) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            query = "SELECT * FROM learner_goals" + ("" if include_archived else " WHERE status='active'") + " ORDER BY created_at DESC"
            rows = conn.execute(query).fetchall()
            items = [_goal_view(conn, row) for row in rows]
        return {"goals": items, "count": len(items)}

    @router.post("/api/goals", status_code=201)
    def create_goal(payload: GoalPayload) -> dict[str, Any]:
        now, goal_id = _stamp(), str(uuid4())
        with connect_database(Path(db_path)) as conn:
            baseline = _activity_count(conn, payload.goal_type)
            conn.execute("INSERT INTO learner_goals (id,title,description,goal_type,target_count,baseline_count,due_date,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,'active',?,?)",
                         (goal_id, payload.title, payload.description, payload.goal_type, payload.target_count, baseline, payload.due_date.isoformat() if payload.due_date else None, now, now))
            row = conn.execute("SELECT * FROM learner_goals WHERE id=?", (goal_id,)).fetchone()
            return {"goal": _goal_view(conn, row)}

    @router.put("/api/goals/{goal_id}")
    def update_goal(goal_id: str, payload: GoalPayload) -> dict[str, Any]:
        now = _stamp()
        with connect_database(Path(db_path)) as conn:
            existing = conn.execute("SELECT * FROM learner_goals WHERE id=?", (goal_id,)).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Goal not found.")
            baseline = existing["baseline_count"] if existing["goal_type"] == payload.goal_type else _activity_count(conn, payload.goal_type)
            conn.execute("UPDATE learner_goals SET title=?,description=?,goal_type=?,target_count=?,baseline_count=?,due_date=?,updated_at=? WHERE id=?",
                         (payload.title, payload.description, payload.goal_type, payload.target_count, baseline, payload.due_date.isoformat() if payload.due_date else None, now, goal_id))
            return {"goal": _goal_view(conn, conn.execute("SELECT * FROM learner_goals WHERE id=?", (goal_id,)).fetchone())}

    @router.post("/api/goals/{goal_id}/archive")
    def archive_goal(goal_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("UPDATE learner_goals SET status='archived',updated_at=? WHERE id=?", (_stamp(), goal_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Goal not found.")
            return {"goal": dict(conn.execute("SELECT * FROM learner_goals WHERE id=?", (goal_id,)).fetchone())}

    @router.post("/api/goals/{goal_id}/restore")
    def restore_goal(goal_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("UPDATE learner_goals SET status='active',updated_at=? WHERE id=?", (_stamp(), goal_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Goal not found.")
            return {"goal": _goal_view(conn, conn.execute("SELECT * FROM learner_goals WHERE id=?", (goal_id,)).fetchone())}

    @router.delete("/api/goals/{goal_id}", status_code=204)
    def delete_goal(goal_id: str) -> None:
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("DELETE FROM learner_goals WHERE id=?", (goal_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Goal not found.")

    return router
