"""Validated, local-only JSON export and transactional restore of learner data."""
from __future__ import annotations

import json
import math
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from prepped.database import connect_database, initialize_database
from prepped.career import initialize_career_database
from prepped.progress import initialize_progress_database

BACKUP_FORMAT = "prepped-local-backup"
BACKUP_FORMAT_VERSION = 1
DATABASE_SCHEMA_VERSION = 3
MAX_BACKUP_BYTES = 25 * 1024 * 1024
MAX_BACKUP_ROWS = 200_000
TABLES = (
    "learner_profile",
    "sessions",
    "answers",
    "learning_attempts",
    "learning_events",
    "learning_memory",
    "learning_memory_reviews",
    "career_sessions",
    "career_turns",
    "learner_goals",
    "recommendation_dismissals",
)
INSERT_ORDER = (
    "learner_profile",
    "sessions",
    "learning_attempts",
    "career_sessions",
    "learner_goals",
    "recommendation_dismissals",
    "answers",
    "learning_events",
    "learning_memory",
    "career_turns",
    "learning_memory_reviews",
)

def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')]

def create_portability_router(db_path: Path) -> APIRouter:
    router = APIRouter()

    @router.get("/api/data/status")
    def data_status() -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            counts = {}
            for table in TABLES:
                counts[table] = int(conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"])
            return {"backup_format": BACKUP_FORMAT, "backup_format_version": BACKUP_FORMAT_VERSION,
                    "database_schema_version": int(conn.execute("PRAGMA user_version").fetchone()[0]),
                    "counts": counts, "maximum_backup_bytes": MAX_BACKUP_BYTES,
                    "note": "Backups contain personal answers and notes. Store them privately; credentials, environment variables, and voice models are not included."}

    @router.get("/api/data/export")
    def export_data() -> Response:
        with connect_database(Path(db_path)) as conn:
            schema_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            counts = {table: int(conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]) for table in TABLES}
            if sum(counts.values()) > MAX_BACKUP_ROWS:
                raise HTTPException(status_code=413, detail="The local database exceeds the 200,000-record backup limit.")
            tables = {
                table: [dict(row) for row in conn.execute(f'SELECT * FROM "{table}"')]
                for table in TABLES
            }
        backup = {"format": BACKUP_FORMAT, "format_version": BACKUP_FORMAT_VERSION,
                  "database_schema_version": schema_version, "app_version": "0.3.0",
                  "exported_at": _stamp(), "tables": tables}
        raw = json.dumps(backup, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(raw) > MAX_BACKUP_BYTES:
            raise HTTPException(status_code=413, detail="The local database is too large for a single JSON backup (25 MB limit).")
        filename = "prepped-backup-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + ".json"
        return Response(content=raw, media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                                 "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @router.post("/api/data/restore")
    async def restore_data(request: Request) -> dict[str, Any]:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BACKUP_BYTES:
                    raise HTTPException(status_code=413, detail="Backup exceeds the 25 MB restore limit.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from exc
        chunks: list[bytes] = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_BACKUP_BYTES:
                raise HTTPException(status_code=413, detail="Backup exceeds the 25 MB restore limit.")
            chunks.append(chunk)
        try:
            payload = json.loads(b"".join(chunks))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise HTTPException(status_code=400, detail="The selected file is not valid Prepped backup JSON.") from exc
        expected_keys = {"format", "format_version", "database_schema_version", "app_version", "exported_at", "tables", "confirm_replace"}
        if not isinstance(payload, dict) or set(payload) != expected_keys or payload.get("format") != BACKUP_FORMAT:
            raise HTTPException(status_code=400, detail="This file is not a complete Prepped backup.")
        if type(payload.get("format_version")) is not int or type(payload.get("database_schema_version")) is not int or payload.get("format_version") != BACKUP_FORMAT_VERSION or payload.get("database_schema_version") != DATABASE_SCHEMA_VERSION:
            raise HTTPException(status_code=409, detail="This backup format or database version is not supported by this Prepped build.")
        if payload.get("confirm_replace") is not True:
            raise HTTPException(status_code=400, detail="Explicit confirmation is required because restore replaces all current local learning data.")
        tables = payload.get("tables")
        if not isinstance(tables, dict) or set(tables) != set(TABLES):
            raise HTTPException(status_code=400, detail="Backup is missing required data tables or contains unsupported tables.")
        total_rows = 0
        for table in TABLES:
            if not isinstance(tables[table], list):
                raise HTTPException(status_code=400, detail=f"Backup table {table} must contain a list of records.")
            total_rows += len(tables[table])
        if total_rows > MAX_BACKUP_ROWS:
            raise HTTPException(status_code=413, detail="Backup contains too many records (200,000 maximum).")

        target_path = Path(db_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix="prepped-restore-") as temp_dir:
                staged_path = Path(temp_dir) / "validated.sqlite3"
                initialize_database(staged_path)
                initialize_career_database(staged_path)
                initialize_progress_database(staged_path)
                with connect_database(staged_path) as staged:
                    column_map = {table: _columns(staged, table) for table in TABLES}
                    for table in TABLES:
                        expected = set(column_map[table])
                        records = tables[table]
                        for index, record in enumerate(records):
                            if not isinstance(record, dict) or set(record) != expected:
                                raise ValueError(f"Record {index + 1} in {table} has an unexpected field set.")
                            if any(not isinstance(value, (str, int, float, bool, type(None))) for value in record.values()):
                                raise ValueError(f"Record {index + 1} in {table} contains a non-scalar value.")
                            if any(
                                (isinstance(value, float) and not math.isfinite(value))
                                or (isinstance(value, int) and not isinstance(value, bool)
                                    and not -(2**63) <= value < 2**63)
                                for value in record.values()
                            ):
                                raise ValueError(f"Record {index + 1} in {table} contains a non-finite or out-of-range number.")
                            if any(isinstance(value, str) and len(value) > 2_000_000 for value in record.values()):
                                raise ValueError(f"Record {index + 1} in {table} contains an oversized text field.")
                    for table in reversed(INSERT_ORDER):
                        staged.execute(f'DELETE FROM "{table}"')
                    for table in INSERT_ORDER:
                        columns = column_map[table]
                        quoted_columns = ",".join(f'"{name}"' for name in columns)
                        placeholders = ",".join("?" for _ in columns)
                        statement = f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})'
                        staged.executemany(statement, [[record[name] for name in columns] for record in tables[table]])
                    violations = staged.execute("PRAGMA foreign_key_check").fetchall()
                    if violations:
                        raise ValueError("Backup contains broken references between saved records.")
                    integrity = staged.execute("PRAGMA integrity_check").fetchone()[0]
                    if integrity != "ok":
                        raise ValueError("Restored database failed its SQLite integrity check.")
                source = sqlite3.connect(staged_path)
                destination = sqlite3.connect(target_path)
                try:
                    source.backup(destination)
                    destination.commit()
                finally:
                    destination.close()
                    source.close()
        except HTTPException:
            raise
        except (sqlite3.Error, ValueError, KeyError, TypeError, OverflowError) as exc:
            raise HTTPException(status_code=422, detail=f"Backup validation failed; current data was not replaced. {exc}") from exc

        return {"restored": True, "records_restored": total_rows,
                "tables": {table: len(tables[table]) for table in TABLES},
                "note": "Local learning data was replaced by the validated backup. Refresh the page to reload it."}

    return router
