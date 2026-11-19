"""Local learner profile API and validation."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

PrimaryGoal = Literal[
    "english_fluency",
    "placement_interviews",
    "technical_interviews",
    "project_communication",
    "professional_communication",
]
ConfidenceLevel = Literal["beginner", "developing", "confident"]
ImprovementArea = Literal[
    "speaking_fluency",
    "grammar",
    "vocabulary",
    "pronunciation",
    "project_explanation",
    "technical_interviews",
    "hr_interviews",
    "professional_communication",
    "confidence",
]


class LearnerProfileUpdate(BaseModel):
    """Complete editable profile; no account or external identity is required."""

    display_name: str | None = Field(default=None, max_length=80)
    study_year: int | None = Field(default=None, ge=1, le=6)
    branch: str | None = Field(default=None, max_length=100)
    primary_goal: PrimaryGoal = "placement_interviews"
    confidence_level: ConfidenceLevel = "developing"
    target_role: str | None = Field(default=None, max_length=120)
    improvement_areas: list[ImprovementArea] = Field(default_factory=list, max_length=9)

    @field_validator("display_name", "branch", "target_role")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _profile_from_row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    profile = dict(row)
    try:
        profile["improvement_areas"] = json.loads(profile.pop("improvement_areas_json"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Saved learner profile is unreadable.") from exc
    return profile


def create_profile_router(db_path: Path) -> APIRouter:
    """Create profile endpoints against the app's injected SQLite database."""
    router = APIRouter()

    @router.get("/api/profile")
    def get_profile() -> dict:
        from prepped.database import connect_database

        with connect_database(Path(db_path)) as connection:
            row = connection.execute("SELECT * FROM learner_profile WHERE id = 1").fetchone()
        profile = _profile_from_row(row)
        return {"configured": profile is not None, "profile": profile}

    @router.put("/api/profile")
    def save_profile(payload: LearnerProfileUpdate) -> dict:
        from prepped.database import connect_database

        now = _now()
        values = payload.model_dump()
        with connect_database(Path(db_path)) as connection:
            connection.execute(
                """
                INSERT INTO learner_profile
                    (id, display_name, study_year, branch, primary_goal, confidence_level,
                     target_role, improvement_areas_json, created_at, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    display_name = excluded.display_name,
                    study_year = excluded.study_year,
                    branch = excluded.branch,
                    primary_goal = excluded.primary_goal,
                    confidence_level = excluded.confidence_level,
                    target_role = excluded.target_role,
                    improvement_areas_json = excluded.improvement_areas_json,
                    updated_at = excluded.updated_at
                """,
                (
                    values["display_name"], values["study_year"], values["branch"],
                    values["primary_goal"], values["confidence_level"], values["target_role"],
                    json.dumps(values["improvement_areas"]), now, now,
                ),
            )
            row = connection.execute("SELECT * FROM learner_profile WHERE id = 1").fetchone()
        profile = _profile_from_row(row)
        return {"configured": True, "profile": profile}

    return router
