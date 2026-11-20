"""Evidence-backed, deterministic learner intelligence and learner-owned plans.

Skill states are derived from existing records on every request. This module does
not persist a second learner profile or infer ability from open responses, voice,
career heuristics, or activity counts.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database
from prepped.learning import DEFAULT_CURRICULUM_PATH, build_recommendations, load_curriculum

CLOSED_EXERCISES = {"choice", "vocabulary", "listening", "ordering"}
STUDIO_SKILLS = {
    "project-explanation": ["communication.project-summary", "communication.clarity",
                            "interview.project-explanation", "interview.readiness"],
    "hr-behavioural": ["interview.hr-behavioural"],
    "technical-fundamentals": ["interview.technical"],
}
PLAN_ITEM_TYPES = {"memory_review", "lesson", "career_practice", "project_practice"}
PLAN_TABLES = """
CREATE TABLE IF NOT EXISTS adaptive_plans (
    plan_date TEXT PRIMARY KEY,
    available_minutes INTEGER NOT NULL CHECK (available_minutes BETWEEN 5 AND 180),
    generated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS adaptive_plan_items (
    id TEXT PRIMARY KEY,
    plan_date TEXT NOT NULL REFERENCES adaptive_plans(plan_date) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK (item_type IN ('memory_review','lesson','career_practice','project_practice')),
    target_id TEXT NOT NULL,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 600),
    estimated_minutes INTEGER NOT NULL CHECK (estimated_minutes BETWEEN 1 AND 180),
    position INTEGER NOT NULL CHECK (position BETWEEN 0 AND 100),
    skipped_at TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(plan_date, item_type, target_id)
);
CREATE INDEX IF NOT EXISTS idx_adaptive_plan_items_date_position
    ON adaptive_plan_items(plan_date, position, created_at);
"""

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds")

def _parse_stamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None

def initialize_intelligence_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as conn:
        conn.executescript(PLAN_TABLES)
        conn.execute("PRAGMA user_version = 4")

class PlanGeneratePayload(BaseModel):
    plan_date: date = Field(default_factory=date.today)
    available_minutes: int = Field(default=30, ge=5, le=180)
    regenerate: bool = False

class WeekGeneratePayload(BaseModel):
    week_start: date = Field(default_factory=lambda: date.today() - timedelta(days=date.today().weekday()))
    available_minutes_per_day: int = Field(default=30, ge=5, le=180)

    @field_validator("week_start")
    @classmethod
    def monday_only(cls, value: date) -> date:
        if value.weekday() != 0:
            raise ValueError("Choose a Monday as the start of the learning week.")
        return value

class PlanItemUpdate(BaseModel):
    skipped: bool | None = None
    position: int | None = Field(default=None, ge=0, le=100)

class PlanItemCreate(BaseModel):
    plan_date: date
    item_type: Literal["lesson", "career_practice", "project_practice"]
    target_id: str = Field(min_length=1, max_length=120)

    @field_validator("target_id")
    @classmethod
    def clean_target(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Choose a valid activity.")
        return value

class RecommendationPreference(BaseModel):
    kind: Literal["lesson", "review_memory", "career_practice", "project_practice"]
    target_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=160)
    reason: str = Field(default="", max_length=500)

    @field_validator("target_id", "title")
    @classmethod
    def clean_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

def _profile(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM learner_profile WHERE id=1").fetchone()
    if row is None:
        return None
    item = dict(row)
    try:
        item["improvement_areas"] = json.loads(item.pop("improvement_areas_json"))
    except (TypeError, json.JSONDecodeError):
        item["improvement_areas"] = []
    return item

def _freshness(value: str | None, now: datetime) -> tuple[str, int | None]:
    parsed = _parse_stamp(value)
    if parsed is None:
        return "unknown", None
    days = max(0, (now - parsed).days)
    if days <= 14:
        return "recent", days
    if days <= 45:
        return "ageing", days
    return "stale", days

def _skill_evidence(conn: sqlite3.Connection, curriculum: dict[str, Any], now: datetime) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    studio_skill_ids = {skill_id for skill_ids in STUDIO_SKILLS.values() for skill_id in skill_ids}
    skills = {item["id"]: item for item in curriculum["skills"]
              if item.get("status", "active") == "active" or item["id"] in studio_skill_ids}
    lessons = {item["id"]: item for item in curriculum["lessons"]}
    evidence: dict[str, list[dict[str, Any]]] = {key: [] for key in skills}
    activity: dict[str, int] = {key: 0 for key in skills}
    objective: dict[str, list[dict[str, Any]]] = {key: [] for key in skills}

    attempts = conn.execute(
        "SELECT id,lesson_id,status,lesson_json,responses_json,feedback_json,started_at,completed_at "
        "FROM learning_attempts ORDER BY COALESCE(completed_at,started_at) DESC"
    ).fetchall()
    attempt_skills: dict[str, list[str]] = {}
    lesson_skills: dict[str, list[str]] = {}
    for row in attempts:
        try:
            lesson = json.loads(row["lesson_json"] or "{}") or lessons.get(row["lesson_id"], {})
            responses = json.loads(row["responses_json"] or "[]")
            feedback = json.loads(row["feedback_json"] or "[]") if row["feedback_json"] else []
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(lesson, dict):
            continue
        skill_ids = [sid for sid in lesson.get("skill_ids", []) if sid in skills]
        if not skill_ids:
            continue
        attempt_skills[row["id"]] = skill_ids
        lesson_skills[row["lesson_id"]] = skill_ids
        exercise_map = {item.get("id"): item for item in lesson.get("exercises", []) if isinstance(item, dict)}
        feedback_map = {item.get("exercise_id"): item for item in feedback if isinstance(item, dict)}
        timestamp = row["completed_at"] or row["started_at"]
        for sid in skill_ids:
            activity[sid] += 1
            evidence[sid].append({
                "source_type": "lesson_attempt", "source_id": row["id"],
                "title": lesson.get("title", row["lesson_id"]),
                "occurred_at": timestamp, "kind": "practice_activity",
                "outcome": "completed" if row["status"] == "completed" else "started",
                "note": "A lesson attempt is activity evidence, not proof of skill.",
            })
        for response in responses if isinstance(responses, list) else []:
            if not isinstance(response, dict):
                continue
            exercise = exercise_map.get(response.get("exercise_id"), {})
            result = feedback_map.get(response.get("exercise_id"), {})
            exercise_type = exercise.get("type")
            if exercise_type not in CLOSED_EXERCISES and exercise_type not in {"reflection", "short_response", "pronunciation"}:
                continue
            outcome = result.get("status") if exercise_type in CLOSED_EXERCISES else "saved_for_self_review"
            event = {
                "source_type": "lesson_response", "source_id": row["id"],
                "title": exercise.get("prompt", response.get("exercise_id", "Lesson response")),
                "occurred_at": timestamp,
                "kind": "closed_exercise_response" if exercise_type in CLOSED_EXERCISES else "open_self_review",
                "outcome": outcome or "unavailable",
                "exercise_id": response.get("exercise_id"),
                "lesson_id": row["lesson_id"],
                "note": ("Correctness is known only for authored closed exercises."
                         if exercise_type in CLOSED_EXERCISES else
                         "Open responses are saved for self-review and are not automatically graded."),
            }
            for sid in skill_ids:
                evidence[sid].append(event)
                if exercise_type in CLOSED_EXERCISES and outcome in {"correct", "review"}:
                    objective[sid].append(event)

    project_rows = conn.execute(
        "SELECT id,status,created_at,completed_at FROM sessions ORDER BY COALESCE(completed_at,created_at) DESC"
    ).fetchall()
    project_skill_ids = ["communication.project-summary", "communication.clarity",
                         "interview.project-explanation", "interview.readiness"]
    project_session_skills: dict[str, list[str]] = {}
    for row in project_rows:
        project_session_skills[row["id"]] = [sid for sid in project_skill_ids if sid in evidence]
        for sid in project_session_skills[row["id"]]:
                activity[sid] += 1
                evidence[sid].append({
                    "source_type": "project_practice", "source_id": row["id"],
                    "title": "Project explanation practice", "occurred_at": row["completed_at"] or row["created_at"],
                    "kind": "practice_activity", "outcome": row["status"],
                    "note": "Practice completion is not an assessment of answer quality.",
                })

    career_rows = conn.execute(
        "SELECT id,studio_id,status,created_at,completed_at FROM career_sessions "
        "ORDER BY COALESCE(completed_at,created_at) DESC"
    ).fetchall()
    career_session_skills: dict[str, list[str]] = {}
    for row in career_rows:
        career_session_skills[row["id"]] = [sid for sid in STUDIO_SKILLS.get(row["studio_id"], []) if sid in evidence]
        for sid in career_session_skills[row["id"]]:
                activity[sid] += 1
                evidence[sid].append({
                    "source_type": "career_session", "source_id": row["id"],
                    "title": row["studio_id"].replace("-", " ").title() + " practice",
                    "occurred_at": row["completed_at"] or row["created_at"],
                    "kind": "practice_activity", "outcome": row["status"],
                    "note": "Interview activity is not scored for correctness or hiring readiness.",
                })

    # Revision records can link to lesson attempts, project-practice sessions,
    # or Career studio sessions. These remain learner-rated activity, never scores.
    revision_rows = conn.execute(
        """SELECT r.id,r.rating,r.reviewed_at,m.source_type,m.source_id,m.source_title
           FROM learning_memory_reviews r JOIN learning_memory m ON m.id=r.item_id
           ORDER BY r.reviewed_at DESC"""
    ).fetchall()
    for row in revision_rows:
        source_id = row["source_id"] or ""
        source_type = row["source_type"]
        if source_type in {"lesson", "lesson_attempt", "learning_attempt"}:
            linked = attempt_skills.get(source_id, []) or lesson_skills.get(source_id, [])
        elif source_type == "practice":
            linked = project_session_skills.get(source_id, [])
        elif source_type == "career_interview":
            linked = career_session_skills.get(source_id, [])
        else:
            linked = []
        for sid in linked:
            activity[sid] += 1
            evidence[sid].append({
                "source_type": "learner_memory_review", "source_id": row["id"],
                "linked_source_id": source_id,
                "title": row["source_title"] or "Learner-saved revision",
                "occurred_at": row["reviewed_at"], "kind": "revision_activity",
                "outcome": row["rating"],
                "note": "A learner-rated revision event; it is not an objective assessment of mastery.",
            })

    output: list[dict[str, Any]] = []
    for sid, skill in skills.items():
        records = sorted(evidence[sid], key=lambda item: item.get("occurred_at") or "", reverse=True)
        closed = objective[sid]
        correct = sum(item["outcome"] == "correct" for item in closed)
        review = sum(item["outcome"] == "review" for item in closed)
        recent_misses: dict[tuple[str, str], int] = {}
        for item in closed:
            stamp = _parse_stamp(item.get("occurred_at"))
            if item["outcome"] == "review" and stamp and 0 <= (now - stamp).days <= 30:
                mistake_key = (item.get("lesson_id") or "", str(item.get("exercise_id") or "unknown"))
                recent_misses[mistake_key] = recent_misses.get(mistake_key, 0) + 1
        repeated = [{"lesson_id": key[0], "exercise_id": key[1], "review_needed_responses": count}
                    for key, count in sorted(recent_misses.items(), key=lambda pair: (-pair[1], pair[0])) if count >= 2]
        latest = records[0]["occurred_at"] if records else None
        freshness, age_days = _freshness(latest, now)
        if not records:
            state = "insufficient_evidence"
        elif not closed:
            state = "practice_recorded"
        elif repeated:
            state = "revisit_suggested"
        elif correct and review:
            state = "mixed_closed_exercise_evidence"
        elif correct >= 2:
            state = "repeated_correct_responses_observed"
        else:
            state = "single_closed_response_observed"
        quantity = len(closed)
        coverage = "none" if not records else ("limited" if quantity < 2 else ("some" if quantity < 5 else "broader"))
        output.append({
            "skill_id": sid, "title": skill["title"], "description": skill["description"],
            "curriculum_status": skill.get("status", "active"),
            "category": skill.get("category", "general"), "prerequisites": skill.get("prerequisites", []),
            "state": state, "state_label": {
                "insufficient_evidence": "Not enough evidence",
                "practice_recorded": "Practice recorded",
                "revisit_suggested": "Revisit suggested",
                "mixed_closed_exercise_evidence": "Mixed exercise evidence",
                "repeated_correct_responses_observed": "Repeated correct responses observed",
                "single_closed_response_observed": "One closed-exercise response observed",
            }[state],
            "activity_count": activity[sid], "closed_response_count": quantity,
            "correct_response_count": correct, "review_needed_count": review,
            "evidence_coverage": coverage, "freshness": freshness, "evidence_age_days": age_days,
            "latest_evidence_at": latest, "repeated_mistakes": repeated,
            "evidence": records[:8],
            "limitations": "This is a trace of saved practice and authored closed-exercise responses, not a proficiency or mastery rating.",
        })
    stats = {
        "skill_count": len(output),
        "skills_with_activity": sum(item["activity_count"] > 0 for item in output),
        "closed_exercise_responses": sum(item["closed_response_count"] for item in output),
        "correct_closed_responses": sum(item["correct_response_count"] for item in output),
        "review_needed_responses": sum(item["review_needed_count"] for item in output),
        "practice_activities": sum(item["activity_count"] for item in output),
    }
    return output, stats

def _active_goals(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    queries = {
        "lessons_completed": "SELECT COUNT(DISTINCT lesson_id) AS n FROM learning_attempts WHERE status='completed' AND lesson_id!='baseline-check'",
        "practice_sessions": "SELECT COUNT(*) AS n FROM sessions WHERE status='completed'",
        "interviews_completed": "SELECT COUNT(*) AS n FROM career_sessions WHERE status='completed'",
        "memory_reviews": "SELECT COUNT(*) AS n FROM learning_memory_reviews",
    }
    output = []
    for row in conn.execute("SELECT id,title,goal_type,target_count,baseline_count,due_date FROM learner_goals WHERE status='active' ORDER BY created_at"):
        item = dict(row)
        current = int(conn.execute(queries[item["goal_type"]]).fetchone()["n"] or 0)
        progress = max(0, current - int(item["baseline_count"]))
        item["current_count"] = progress
        item["remaining"] = max(0, int(item["target_count"]) - progress)
        output.append(item)
    return output

def _recommendations(conn: sqlite3.Connection, curriculum: dict[str, Any], skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profile = _profile(conn)
    route = build_recommendations(curriculum, profile)
    completed = {row["lesson_id"] for row in conn.execute(
        "SELECT lesson_id FROM learning_attempts WHERE status='completed'"
    ).fetchall()}
    by_skill = {item["skill_id"]: item for item in skills}
    lessons = {item["id"]: item for item in curriculum["lessons"]}
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for skill in skills:
        for mistake in skill["repeated_mistakes"]:
            lesson = lessons.get(mistake["lesson_id"]) or next((item for item in curriculum["lessons"]
                           if skill["skill_id"] in item.get("skill_ids", [])), None)
            if lesson:
                key = "lesson:" + lesson["id"]
                if key not in seen:
                    candidates.append({"kind": "lesson", "target_id": lesson["id"],
                        "title": lesson["title"], "reason": f"Two or more recent authored closed-exercise responses for {skill['title']} needed review. Revisit the lesson and its explanations.",
                        "estimated_minutes": lesson.get("estimated_minutes", 8), "source": "repeated_observed_response"})
                    seen.add(key)
    for skill in skills:
        if skill.get("curriculum_status") == "planned":
            continue
        for prerequisite in skill["prerequisites"]:
            prereq_state = by_skill.get(prerequisite)
            if prereq_state and prereq_state["closed_response_count"] == 0:
                lesson = next((item for item in curriculum["lessons"]
                               if prerequisite in item.get("skill_ids", [])), None)
                if lesson:
                    key = "lesson:" + lesson["id"]
                    if key not in seen and lesson["id"] not in completed:
                        candidates.append({"kind": "lesson", "target_id": lesson["id"],
                            "title": lesson["title"], "reason": f"This is a declared prerequisite for {skill['title']}; there is not yet saved practice evidence for it.",
                            "estimated_minutes": lesson.get("estimated_minutes", 8), "source": "declared_prerequisite"})
                        seen.add(key)
    for item in route["items"]:
        lesson = lessons[item["lesson_id"]]
        if lesson["id"] in completed:
            continue
        key = "lesson:" + lesson["id"]
        if key not in seen:
            candidates.append({"kind": "lesson", "target_id": lesson["id"], "title": lesson["title"],
                "reason": item["why"], "estimated_minutes": lesson.get("estimated_minutes", 8),
                "source": "learner_goal_route"})
            seen.add(key)
    profile_goal = profile.get("primary_goal") if profile else "placement_interviews"
    default_studio = "technical-fundamentals" if profile_goal == "technical_interviews" else "project-explanation"
    for goal in _active_goals(conn):
        if goal["remaining"] <= 0:
            continue
        if goal["goal_type"] == "interviews_completed":
            key = "career_practice:" + default_studio
            if key not in seen:
                candidates.insert(0, {"kind": "career_practice", "target_id": default_studio,
                    "title": "Interview practice for: " + goal["title"],
                    "reason": f"This activity supports your active goal ({goal['current_count']} of {goal['target_count']} completed).",
                    "estimated_minutes": 15, "source": "active_learner_goal", "goal_id": goal["id"]})
                seen.add(key)
        elif goal["goal_type"] == "practice_sessions":
            key = "project_practice:project-explanation"
            if key not in seen:
                candidates.insert(0, {"kind": "project_practice", "target_id": "project-explanation",
                    "title": "Project explanation practice for: " + goal["title"],
                    "reason": f"This activity supports your active goal ({goal['current_count']} of {goal['target_count']} completed).",
                    "estimated_minutes": 15, "source": "active_learner_goal", "goal_id": goal["id"]})
                seen.add(key)
    now = _now()
    due = conn.execute(
        "SELECT id,front,due_at FROM learning_memory WHERE status='active' AND dismissed_at IS NULL AND due_at<=? ORDER BY due_at LIMIT 5",
        (_stamp(now),),
    ).fetchall()
    for item in due:
        candidates.insert(0, {"kind": "review_memory", "target_id": item["id"],
            "title": ("Review: " + item["front"])[:160], "reason": "This learner-saved item is due for revision.",
            "estimated_minutes": 5, "source": "due_memory"})
    dismissed = {row["recommendation_key"] for row in conn.execute(
        "SELECT recommendation_key FROM recommendation_dismissals"
    ).fetchall()}
    return [item for item in candidates if f"{item['kind']}:{item['target_id']}" not in dismissed][:12]

def _item_completed(conn: sqlite3.Connection, item: sqlite3.Row, generated_at: str) -> bool:
    if item["item_type"] == "memory_review":
        return conn.execute(
            "SELECT 1 FROM learning_memory_reviews WHERE item_id=? AND reviewed_at>=? LIMIT 1",
            (item["target_id"], generated_at),
        ).fetchone() is not None
    if item["item_type"] == "lesson":
        return conn.execute(
            "SELECT 1 FROM learning_attempts WHERE lesson_id=? AND status='completed' AND completed_at>=? LIMIT 1",
            (item["target_id"], generated_at),
        ).fetchone() is not None
    if item["item_type"] == "career_practice":
        return conn.execute(
            "SELECT 1 FROM career_sessions WHERE studio_id=? AND status='completed' AND completed_at>=? LIMIT 1",
            (item["target_id"], generated_at),
        ).fetchone() is not None
    return conn.execute(
        "SELECT 1 FROM sessions WHERE status='completed' AND completed_at>=? LIMIT 1",
        (generated_at,),
    ).fetchone() is not None

def _plan_view(conn: sqlite3.Connection, plan: sqlite3.Row) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM adaptive_plan_items WHERE plan_date=? ORDER BY position,created_at,id",
        (plan["plan_date"],),
    ).fetchall()
    items = []
    for row in rows:
        completed = _item_completed(conn, row, row["created_at"])
        status = "completed" if completed else ("skipped" if row["skipped_at"] else "planned")
        items.append({**dict(row), "status": status, "self_reported": False,
                      "action_note": "Completion is reflected only after the linked lesson, review, or practice session is saved."})
    return {"plan_date": plan["plan_date"], "available_minutes": plan["available_minutes"],
            "generated_at": plan["generated_at"], "items": items,
            "estimated_minutes": sum(item["estimated_minutes"] for item in items if item["status"] != "skipped"),
            "completed_count": sum(item["status"] == "completed" for item in items),
            "skipped_count": sum(item["status"] == "skipped" for item in items),
            "note": "Items are suggestions. Completion is derived from saved source activity, not a self-awarded skill score."}

def _ensure_plan(conn: sqlite3.Connection, plan_date: date, minutes: int) -> sqlite3.Row:
    existing = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (plan_date.isoformat(),)).fetchone()
    if existing is None:
        conn.execute("INSERT INTO adaptive_plans(plan_date,available_minutes,generated_at) VALUES (?,?,?)",
                     (plan_date.isoformat(), minutes, _stamp()))
    return conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (plan_date.isoformat(),)).fetchone()

def _add_plan_item(conn: sqlite3.Connection, plan_date: date, item_type: str, target_id: str,
                   title: str, reason: str, minutes: int) -> None:
    existing = conn.execute(
        "SELECT 1 FROM adaptive_plan_items WHERE plan_date=? AND item_type=? AND target_id=?",
        (plan_date.isoformat(), item_type, target_id),
    ).fetchone()
    if existing:
        return
    plan = conn.execute("SELECT available_minutes FROM adaptive_plans WHERE plan_date=?", (plan_date.isoformat(),)).fetchone()
    used = conn.execute(
        "SELECT COALESCE(SUM(estimated_minutes),0) AS n FROM adaptive_plan_items WHERE plan_date=? AND skipped_at IS NULL",
        (plan_date.isoformat(),),
    ).fetchone()["n"]
    if plan and int(used) + minutes > int(plan["available_minutes"]):
        raise HTTPException(status_code=422, detail="This activity would exceed the day's available time. Increase the time budget or remove another activity.")
    count = conn.execute("SELECT COUNT(*) AS n FROM adaptive_plan_items WHERE plan_date=?", (plan_date.isoformat(),)).fetchone()["n"]
    conn.execute(
        """INSERT OR IGNORE INTO adaptive_plan_items
           (id,plan_date,item_type,target_id,title,reason,estimated_minutes,position,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (str(uuid4()), plan_date.isoformat(), item_type, target_id, title[:200], reason[:600],
         max(1, min(180, minutes)), min(100, int(count)), _stamp()),
    )

def _generate_day(conn: sqlite3.Connection, curriculum: dict[str, Any], plan_date: date,
                  minutes: int, used_memory: set[str] | None = None,
                  used_lessons: set[str] | None = None, include_career: bool = True,
                  include_project: bool = True) -> dict[str, Any]:
    plan = _ensure_plan(conn, plan_date, minutes)
    skills, _ = _skill_evidence(conn, curriculum, _now())
    recommendations = _recommendations(conn, curriculum, skills)
    current = _plan_view(conn, plan)
    used_memory = used_memory if used_memory is not None else set()
    used_lessons = used_lessons if used_lessons is not None else set()
    for existing_item in current["items"]:
        if existing_item["item_type"] == "lesson":
            used_lessons.add(existing_item["target_id"])
        elif existing_item["item_type"] == "memory_review":
            used_memory.add(existing_item["target_id"])
    if any(item["status"] == "planned" for item in current["items"]):
        return current
    # Preserve completed and skipped work on regeneration; only pending items are replaceable.
    if current["items"]:
        for item in current["items"]:
            if item["status"] == "completed" or item["status"] == "skipped":
                continue
            conn.execute("DELETE FROM adaptive_plan_items WHERE id=?", (item["id"],))
    used_minutes = conn.execute(
        "SELECT COALESCE(SUM(estimated_minutes),0) AS n FROM adaptive_plan_items WHERE plan_date=? AND skipped_at IS NULL",
        (plan_date.isoformat(),),
    ).fetchone()["n"]
    remaining = max(0, int(plan["available_minutes"]) - int(used_minutes))
    day_end = datetime.combine(plan_date + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat()
    due_rows = conn.execute(
        "SELECT id,front FROM learning_memory WHERE status='active' AND dismissed_at IS NULL AND due_at<? ORDER BY due_at LIMIT 10",
        (day_end,),
    ).fetchall()
    daily_reviews = 0
    for item in due_rows:
        # Reserve enough time for a focused lesson instead of letting a large
        # review backlog consume the entire daily plan.
        if item["id"] in used_memory or remaining < 25 or daily_reviews >= 2:
            continue
        _add_plan_item(conn, plan_date, "memory_review", item["id"], "Review: " + item["front"],
                       "This learner-saved item is due on or before this day.", 5)
        used_memory.add(item["id"])
        daily_reviews += 1
        remaining -= 5
    lesson = next((item for item in recommendations if item["kind"] == "lesson"
                   and item["target_id"] not in used_lessons), None)
    if lesson and remaining >= lesson["estimated_minutes"]:
        _add_plan_item(conn, plan_date, "lesson", lesson["target_id"], lesson["title"],
                       lesson["reason"], lesson["estimated_minutes"])
        used_lessons.add(lesson["target_id"])
        remaining -= lesson["estimated_minutes"]
    profile = _profile(conn)
    goal = profile.get("primary_goal") if profile else "placement_interviews"
    active_goals = _active_goals(conn)
    interview_goal = any(item["goal_type"] == "interviews_completed" and item["remaining"] > 0 for item in active_goals)
    project_goal = any(item["goal_type"] == "practice_sessions" and item["remaining"] > 0 for item in active_goals)
    if include_career and (goal in {"placement_interviews", "technical_interviews"} or interview_goal) and remaining >= 15:
        recent = conn.execute(
            "SELECT 1 FROM career_sessions WHERE status='completed' AND completed_at>=? LIMIT 1",
            (_stamp(_now() - timedelta(days=14)),),
        ).fetchone()
        if not recent:
            studio = "technical-fundamentals" if goal == "technical_interviews" else "project-explanation"
            _add_plan_item(conn, plan_date, "career_practice", studio,
                           "Practise an interview scenario",
                           "This optional session matches your saved interview-preparation goal.", 15)
            remaining -= 15
    if include_project and project_goal and remaining >= 15:
        _add_plan_item(conn, plan_date, "project_practice", "project-explanation",
                       "Project explanation practice",
                       "This practice supports your active project-practice goal.", 15)
    return _plan_view(conn, conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (plan_date.isoformat(),)).fetchone())

def _overview(conn: sqlite3.Connection, curriculum: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    skills, stats = _skill_evidence(conn, curriculum, now)
    recommendations = _recommendations(conn, curriculum, skills)
    due = conn.execute(
        "SELECT COUNT(*) AS n FROM learning_memory WHERE status='active' AND dismissed_at IS NULL AND due_at<=?",
        (_stamp(now),),
    ).fetchone()["n"]
    reviews = conn.execute("SELECT COUNT(*) AS n FROM learning_memory_reviews").fetchone()["n"]
    revision_ratings = {row["rating"]: int(row["n"]) for row in conn.execute(
        "SELECT rating,COUNT(*) AS n FROM learning_memory_reviews GROUP BY rating"
    )}
    activity = []
    for offset in range(29, -1, -1):
        day = now.date() - timedelta(days=offset)
        next_day = day + timedelta(days=1)
        count = conn.execute(
            "SELECT (SELECT COUNT(*) FROM learning_events WHERE occurred_at>=? AND occurred_at<?) + "
            "(SELECT COUNT(*) FROM sessions WHERE completed_at>=? AND completed_at<?) + "
            "(SELECT COUNT(*) FROM career_sessions WHERE completed_at>=? AND completed_at<?) + "
            "(SELECT COUNT(*) FROM learning_memory_reviews WHERE reviewed_at>=? AND reviewed_at<?) AS n",
            (day.isoformat(), next_day.isoformat(), day.isoformat(), next_day.isoformat(),
             day.isoformat(), next_day.isoformat(), day.isoformat(), next_day.isoformat()),
        ).fetchone()["n"]
        activity.append({"date": day.isoformat(), "count": int(count)})
    return {"generated_at": _stamp(now), "summary": {**stats, "due_memory_items": int(due),
            "memory_reviews": int(reviews), "revision_ratings": revision_ratings,
            "evidence_note": "Activity, closed-exercise responses, and open self-review are kept distinct."},
            "active_goals": _active_goals(conn), "skills": skills, "recommendations": recommendations, "activity_30_days": activity,
            "guardrails": ["No composite ability or mastery score.", "Open responses and career feedback are not automatically graded.",
                           "Skill states are derived from saved local evidence and show freshness and coverage limits."]}

def create_intelligence_router(db_path: Path, curriculum_path: Path = DEFAULT_CURRICULUM_PATH) -> APIRouter:
    router = APIRouter(prefix="/api/intelligence", tags=["adaptive learning intelligence"])

    def data() -> dict[str, Any]:
        try:
            return load_curriculum(Path(curriculum_path))
        except ValueError as exc:
            raise HTTPException(status_code=500, detail="The installed curriculum could not be loaded.") from exc

    @router.get("/overview")
    def overview() -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            return _overview(conn, data())

    @router.get("/catalog")
    def activity_catalog() -> dict[str, Any]:
        curriculum = data()
        return {
            "lessons": [{"id": item["id"], "title": item["title"],
                         "estimated_minutes": item.get("estimated_minutes", 8)}
                        for item in curriculum["lessons"] if item.get("kind") != "diagnostic"],
            "career_studios": [{"id": key, "title": key.replace("-", " ").title()}
                               for key in STUDIO_SKILLS],
            "project_practice": {"id": "project-explanation", "title": "Project explanation practice"},
        }

    @router.get("/plan")
    def daily_plan(plan_date: date | None = Query(default=None)) -> dict[str, Any]:
        plan_date = plan_date or date.today()
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (plan_date.isoformat(),)).fetchone()
            return {"plan": _plan_view(conn, row) if row else None, "plan_date": plan_date.isoformat()}

    @router.post("/plan/generate")
    def generate_plan(payload: PlanGeneratePayload) -> dict[str, Any]:
        if payload.plan_date < date.today() - timedelta(days=1) or payload.plan_date > date.today() + timedelta(days=90):
            raise HTTPException(status_code=422, detail="Choose a plan date from yesterday through the next 90 days.")
        with connect_database(Path(db_path)) as conn:
            plan = _ensure_plan(conn, payload.plan_date, payload.available_minutes)
            if payload.regenerate:
                conn.execute("UPDATE adaptive_plans SET available_minutes=? WHERE plan_date=?",
                             (payload.available_minutes, payload.plan_date.isoformat()))
                plan = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (payload.plan_date.isoformat(),)).fetchone()
                rows = conn.execute("SELECT * FROM adaptive_plan_items WHERE plan_date=?", (payload.plan_date.isoformat(),)).fetchall()
                for item in rows:
                    if item["skipped_at"] is None and not _item_completed(conn, item, item["created_at"]):
                        conn.execute("DELETE FROM adaptive_plan_items WHERE id=?", (item["id"],))
            result = _generate_day(conn, data(), payload.plan_date, payload.available_minutes)
            return {"plan": result}

    @router.get("/plan/week")
    def weekly_plan(week_start: date | None = Query(default=None)) -> dict[str, Any]:
        week_start = week_start or (date.today() - timedelta(days=date.today().weekday()))
        if week_start.weekday() != 0:
            raise HTTPException(status_code=422, detail="Choose a Monday as the start of the learning week.")
        with connect_database(Path(db_path)) as conn:
            days = []
            for offset in range(7):
                target = week_start + timedelta(days=offset)
                row = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (target.isoformat(),)).fetchone()
                days.append(_plan_view(conn, row) if row else {"plan_date": target.isoformat(), "available_minutes": 30, "generated_at": None, "items": [], "estimated_minutes": 0, "completed_count": 0, "skipped_count": 0})
        return {"week_start": week_start.isoformat(), "days": days}

    @router.post("/plan/week/generate")
    def generate_week(payload: WeekGeneratePayload) -> dict[str, Any]:
        if payload.week_start < date.today() - timedelta(days=7) or payload.week_start > date.today() + timedelta(days=90):
            raise HTTPException(status_code=422, detail="Choose a week from last week through the next 90 days.")
        with connect_database(Path(db_path)) as conn:
            used_memory: set[str] = set()
            used_lessons: set[str] = set()
            days = []
            for offset in range(7):
                target = payload.week_start + timedelta(days=offset)
                plan = _ensure_plan(conn, target, payload.available_minutes_per_day)
                conn.execute("UPDATE adaptive_plans SET available_minutes=? WHERE plan_date=?",
                             (payload.available_minutes_per_day, target.isoformat()))
                existing_items = conn.execute(
                    "SELECT * FROM adaptive_plan_items WHERE plan_date=?", (target.isoformat(),)
                ).fetchall()
                for existing_item in existing_items:
                    if _item_completed(conn, existing_item, existing_item["created_at"]):
                        if existing_item["item_type"] == "lesson":
                            used_lessons.add(existing_item["target_id"])
                        elif existing_item["item_type"] == "memory_review":
                            used_memory.add(existing_item["target_id"])
                    elif existing_item["skipped_at"] is None:
                        conn.execute("DELETE FROM adaptive_plan_items WHERE id=?", (existing_item["id"],))
                days.append(_generate_day(conn, data(), target, payload.available_minutes_per_day,
                                          used_memory, used_lessons, include_career=(offset == 4),
                                          include_project=(offset == 2)))
        return {"week_start": payload.week_start.isoformat(), "days": days}

    @router.post("/plan/items", status_code=201)
    def add_plan_item(payload: PlanItemCreate) -> dict[str, Any]:
        curriculum = data()
        with connect_database(Path(db_path)) as conn:
            plan = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (payload.plan_date.isoformat(),)).fetchone()
            if plan is None:
                raise HTTPException(status_code=404, detail="Generate the day's plan before adding an activity.")
            if payload.item_type == "lesson":
                lesson = next((item for item in curriculum["lessons"] if item["id"] == payload.target_id), None)
                if lesson is None:
                    raise HTTPException(status_code=404, detail="Lesson not found.")
                _add_plan_item(conn, payload.plan_date, "lesson", lesson["id"], lesson["title"],
                               "Added by you. You can choose a different activity at any time.", lesson.get("estimated_minutes", 8))
            elif payload.item_type == "career_practice":
                if payload.target_id not in STUDIO_SKILLS:
                    raise HTTPException(status_code=404, detail="Interview studio not found.")
                _add_plan_item(conn, payload.plan_date, "career_practice", payload.target_id,
                               payload.target_id.replace("-", " ").title(),
                               "Added by you to your learning plan.", 15)
            else:
                if payload.target_id != "project-explanation":
                    raise HTTPException(status_code=404, detail="Project practice scenario not found.")
                _add_plan_item(conn, payload.plan_date, "project_practice", payload.target_id,
                               "Project explanation practice", "Added by you to your learning plan.", 15)
            return {"plan": _plan_view(conn, plan)}

    @router.patch("/plan/items/{item_id}")
    def update_plan_item(item_id: str, payload: PlanItemUpdate) -> dict[str, Any]:
        if payload.skipped is None and payload.position is None:
            raise HTTPException(status_code=422, detail="Choose whether to skip an item or change its position.")
        with connect_database(Path(db_path)) as conn:
            item = conn.execute("SELECT * FROM adaptive_plan_items WHERE id=?", (item_id,)).fetchone()
            if item is None:
                raise HTTPException(status_code=404, detail="Plan item not found.")
            if payload.skipped is not None:
                if payload.skipped is False and item["skipped_at"] is not None:
                    plan_budget = conn.execute("SELECT available_minutes FROM adaptive_plans WHERE plan_date=?", (item["plan_date"],)).fetchone()["available_minutes"]
                    used = conn.execute(
                        "SELECT COALESCE(SUM(estimated_minutes),0) AS n FROM adaptive_plan_items WHERE plan_date=? AND skipped_at IS NULL AND id<>?",
                        (item["plan_date"], item_id),
                    ).fetchone()["n"]
                    if int(used) + int(item["estimated_minutes"]) > int(plan_budget):
                        raise HTTPException(status_code=422, detail="Restoring this item would exceed the day's available time. Increase the time budget or skip another activity.")
                conn.execute("UPDATE adaptive_plan_items SET skipped_at=? WHERE id=?",
                             (_stamp() if payload.skipped else None, item_id))
            if payload.position is not None:
                siblings = conn.execute(
                    "SELECT id FROM adaptive_plan_items WHERE plan_date=? ORDER BY position,created_at,id",
                    (item["plan_date"],),
                ).fetchall()
                ordered = [row["id"] for row in siblings]
                ordered.remove(item_id)
                ordered.insert(min(payload.position, len(ordered)), item_id)
                for index, sibling_id in enumerate(ordered):
                    conn.execute("UPDATE adaptive_plan_items SET position=? WHERE id=?", (index, sibling_id))
            plan = conn.execute("SELECT * FROM adaptive_plans WHERE plan_date=?", (item["plan_date"],)).fetchone()
            return {"plan": _plan_view(conn, plan)}

    @router.post("/recommendations/dismiss")
    def dismiss(payload: RecommendationPreference) -> dict[str, Any]:
        key = f"{payload.kind}:{payload.target_id}"
        with connect_database(Path(db_path)) as conn:
            conn.execute(
                """INSERT INTO recommendation_dismissals
                   (recommendation_key,kind,target_id,title,reason,dismissed_at) VALUES (?,?,?,?,?,?)
                   ON CONFLICT(recommendation_key) DO UPDATE SET title=excluded.title,reason=excluded.reason,dismissed_at=excluded.dismissed_at""",
                (key, payload.kind, payload.target_id, payload.title, payload.reason, _stamp()),
            )
        return {"dismissed": True, "recommendation_key": key}

    @router.post("/recommendations/restore")
    def restore(payload: RecommendationPreference) -> dict[str, Any]:
        key = f"{payload.kind}:{payload.target_id}"
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("DELETE FROM recommendation_dismissals WHERE recommendation_key=?", (key,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Dismissed recommendation not found.")
        return {"restored": True, "recommendation_key": key}

    return router
