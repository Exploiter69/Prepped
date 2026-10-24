"""SQLite persistence for local Prepped practice sessions."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def connect_database(db_path: Path) -> sqlite3.Connection:
    """Open a connection with SQLite integrity checks enabled."""
    connection = sqlite3.connect(Path(db_path), timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(db_path: Path) -> None:
    """Create tables and add compatible columns to databases from the starter."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with connect_database(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                scenario_version TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'cancelled')),
                created_at TEXT NOT NULL,
                completed_at TEXT,
                scenario_json TEXT NOT NULL DEFAULT '{}',
                rubric_json TEXT NOT NULL DEFAULT '[]',
                attempt_group_id TEXT,
                attempt_number INTEGER NOT NULL DEFAULT 1 CHECK (attempt_number >= 1)
            );

            CREATE TABLE IF NOT EXISTS answers (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                question_id TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                position INTEGER NOT NULL CHECK (position >= 0),
                created_at TEXT NOT NULL,
                UNIQUE (session_id, position),
                UNIQUE (session_id, question_id)
            );
            """
        )

        session_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(sessions)")
        }
        migrations = {
            "scenario_json": "TEXT NOT NULL DEFAULT '{}'",
            "rubric_json": "TEXT NOT NULL DEFAULT '[]'",
            "attempt_group_id": "TEXT",
            "attempt_number": "INTEGER NOT NULL DEFAULT 1",
        }
        for name, definition in migrations.items():
            if name not in session_columns:
                connection.execute(f"ALTER TABLE sessions ADD COLUMN {name} {definition}")

        connection.execute(
            "UPDATE sessions SET attempt_group_id = id WHERE attempt_group_id IS NULL OR attempt_group_id = ''"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_answers_session_position ON answers(session_id, position)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_attempt_group ON sessions(attempt_group_id, attempt_number)"
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a SQLite row to a plain dictionary."""
    return dict(row) if row is not None else None
