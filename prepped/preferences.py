"""Local learner preferences: TTS playback speed, theme, text size, and replay rules."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from prepped.database import connect_database

ThemeChoice = Literal["light", "dark", "system"]
TextSizeChoice = Literal["normal", "large"]

PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS learner_preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    tts_speed REAL NOT NULL DEFAULT 1.0 CHECK (tts_speed BETWEEN 0.7 AND 1.5),
    theme TEXT NOT NULL DEFAULT 'light' CHECK (theme IN ('light', 'dark', 'system')),
    text_size TEXT NOT NULL DEFAULT 'normal' CHECK (text_size IN ('normal', 'large')),
    ephemeral_audio_replay INTEGER NOT NULL DEFAULT 1 CHECK (ephemeral_audio_replay IN (0, 1)),
    updated_at TEXT NOT NULL
);
"""

DEFAULT_PREFERENCES: dict[str, Any] = {
    "tts_speed": 1.0,
    "theme": "light",
    "text_size": "normal",
    "ephemeral_audio_replay": True,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_preferences_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as conn:
        conn.executescript(PREFERENCES_TABLE)


class PreferencesUpdate(BaseModel):
    tts_speed: float = Field(default=1.0, ge=0.7, le=1.5)
    theme: ThemeChoice = "light"
    text_size: TextSizeChoice = "normal"
    ephemeral_audio_replay: bool = True


def load_preferences(db_path: Path) -> dict[str, Any]:
    with connect_database(Path(db_path)) as conn:
        row = conn.execute("SELECT * FROM learner_preferences WHERE id = 1").fetchone()
    if row is None:
        return {**DEFAULT_PREFERENCES, "updated_at": None}
    return {
        "tts_speed": round(float(row["tts_speed"]), 2),
        "theme": row["theme"],
        "text_size": row["text_size"],
        "ephemeral_audio_replay": bool(row["ephemeral_audio_replay"]),
        "updated_at": row["updated_at"],
    }


def create_preferences_router(db_path: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/api/preferences")
    def get_preferences() -> dict[str, Any]:
        return {"preferences": load_preferences(Path(db_path))}

    @router.put("/api/preferences")
    def save_preferences(payload: PreferencesUpdate) -> dict[str, Any]:
        now = _now()
        speed = round(float(payload.tts_speed), 2)
        with connect_database(Path(db_path)) as conn:
            conn.execute(
                """
                INSERT INTO learner_preferences
                    (id, tts_speed, theme, text_size, ephemeral_audio_replay, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    tts_speed = excluded.tts_speed,
                    theme = excluded.theme,
                    text_size = excluded.text_size,
                    ephemeral_audio_replay = excluded.ephemeral_audio_replay,
                    updated_at = excluded.updated_at
                """,
                (speed, payload.theme, payload.text_size, int(payload.ephemeral_audio_replay), now),
            )
        return {"preferences": load_preferences(Path(db_path))}

    return router
