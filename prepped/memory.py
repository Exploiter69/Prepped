"""Learner-controlled local memory and transparent spaced revision."""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database

ItemType = Literal["word", "phrase", "correction", "concept", "example"]
Rating = Literal["again", "hard", "good", "easy"]
Status = Literal["active", "suspended"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat(timespec="seconds")


def _normalise(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


class CreateMemoryItem(BaseModel):
    item_type: ItemType
    front: str = Field(min_length=1, max_length=240)
    back: str = Field(min_length=1, max_length=2000)
    source_type: str = Field(default="manual", max_length=40)
    source_id: str | None = Field(default=None, max_length=120)
    source_title: str | None = Field(default=None, max_length=200)
    source_excerpt: str | None = Field(default=None, max_length=1000)

    @field_validator("front", "back", "source_type")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("source_id", "source_title", "source_excerpt")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class UpdateMemoryItem(BaseModel):
    item_type: ItemType | None = None
    front: str | None = Field(default=None, min_length=1, max_length=240)
    back: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("front", "back")
    @classmethod
    def trim_update(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class ReviewSubmission(BaseModel):
    rating: Rating


def _item(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _next_interval(repetitions: int, interval_days: int, rating: Rating) -> tuple[int, int]:
    """Small deterministic scheduler; intervals are intentionally explainable, not FSRS."""
    if rating == "again":
        return 0, 1
    if rating == "hard":
        return repetitions + 1, max(1, round(max(interval_days, 1) * 1.2))
    if rating == "easy":
        if repetitions == 0:
            return 1, 3
        return repetitions + 1, max(2, round(max(interval_days, 1) * 2.5))
    if repetitions == 0:
        return 1, 1
    if repetitions == 1:
        return 2, 3
    return repetitions + 1, max(1, interval_days * 2)


def create_memory_router(db_path: Path) -> APIRouter:
    router = APIRouter(prefix="/api/memory", tags=["learning memory"])

    @router.get("/items")
    def list_items(status: Literal["active", "suspended", "all"] = Query(default="active")) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            if status == "all":
                rows = conn.execute("SELECT * FROM learning_memory ORDER BY updated_at DESC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM learning_memory WHERE status = ? ORDER BY due_at, updated_at DESC", (status,)).fetchall()
        return {"items": [_item(row) for row in rows], "count": len(rows)}

    @router.post("/items", status_code=201)
    def create_item(payload: CreateMemoryItem) -> dict[str, Any]:
        now = _stamp()
        item_id = str(uuid4())
        with connect_database(Path(db_path)) as conn:
            duplicate = conn.execute(
                """SELECT id FROM learning_memory
                   WHERE item_type = ? AND normalised_front = ? AND status != 'deleted'
                   LIMIT 1""",
                (payload.item_type, _normalise(payload.front)),
            ).fetchone()
            if duplicate:
                raise HTTPException(status_code=409, detail={
                    "message": "A matching memory item already exists. Edit or reopen the existing item instead.",
                    "existing_id": duplicate["id"],
                })
            conn.execute(
                """INSERT INTO learning_memory
                   (id, item_type, front, back, normalised_front, source_type, source_id,
                    source_title, source_excerpt, status, created_at, updated_at, due_at,
                    interval_days, repetitions, lapses, last_reviewed_at, last_rating)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, 0, 0, 0, NULL, NULL)""",
                (item_id, payload.item_type, payload.front, payload.back, _normalise(payload.front),
                 payload.source_type, payload.source_id, payload.source_title, payload.source_excerpt,
                 now, now, now),
            )
            row = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
        return {"item": _item(row)}

    @router.get("/items/{item_id}")
    def get_item(item_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Memory item not found.")
        return {"item": _item(row)}

    @router.put("/items/{item_id}")
    def update_item(item_id: str, payload: UpdateMemoryItem) -> dict[str, Any]:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(status_code=422, detail="Provide at least one field to update.")
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Memory item not found.")
            front = changes.get("front", row["front"])
            item_type = changes.get("item_type", row["item_type"])
            duplicate = conn.execute(
                """SELECT id FROM learning_memory WHERE item_type = ? AND normalised_front = ?
                   AND id != ? AND status != 'deleted' LIMIT 1""",
                (item_type, _normalise(front), item_id),
            ).fetchone()
            if duplicate:
                raise HTTPException(status_code=409, detail={
                    "message": "Another memory item already uses this term or phrase.",
                    "existing_id": duplicate["id"],
                })
            assignments = ["updated_at = ?", "normalised_front = ?"]
            values: list[Any] = [_stamp(), _normalise(front)]
            for field in ("item_type", "front", "back"):
                if field in changes:
                    assignments.append(f"{field} = ?")
                    values.append(changes[field])
            values.append(item_id)
            conn.execute(f"UPDATE learning_memory SET {', '.join(assignments)} WHERE id = ?", values)
            updated = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
        return {"item": _item(updated)}

    @router.patch("/items/{item_id}/status")
    def set_status(item_id: str, status: Status) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("UPDATE learning_memory SET status = ?, updated_at = ? WHERE id = ?",
                                  (status, _stamp(), item_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Memory item not found.")
            row = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
        return {"item": _item(row)}

    @router.delete("/items/{item_id}", status_code=204)
    def delete_item(item_id: str) -> None:
        with connect_database(Path(db_path)) as conn:
            cursor = conn.execute("DELETE FROM learning_memory WHERE id = ?", (item_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Memory item not found.")

    @router.get("/review/queue")
    def review_queue(limit: int = Query(default=50, ge=1, le=100)) -> dict[str, Any]:
        now = _stamp()
        with connect_database(Path(db_path)) as conn:
            rows = conn.execute(
                """SELECT * FROM learning_memory WHERE status = 'active' AND due_at <= ?
                   ORDER BY due_at ASC, created_at ASC LIMIT ?""",
                (now, limit),
            ).fetchall()
        return {"items": [_item(row) for row in rows], "count": len(rows),
                "as_of": now, "note": "Due dates use the local app's UTC clock. Ratings change only this card's next review date."}

    @router.post("/items/{item_id}/review")
    def review_item(item_id: str, payload: ReviewSubmission) -> dict[str, Any]:
        now = _now()
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Memory item not found.")
            if row["status"] != "active":
                raise HTTPException(status_code=409, detail="Resume this suspended item before reviewing it.")
            repetitions, interval = _next_interval(row["repetitions"], row["interval_days"], payload.rating)
            due = now + timedelta(days=interval)
            reviewed_at, due_at = _stamp(now), _stamp(due)
            conn.execute(
                """INSERT INTO learning_memory_reviews
                   (id, item_id, rating, reviewed_at, previous_due_at, next_due_at, interval_days)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid4()), item_id, payload.rating, reviewed_at, row["due_at"], due_at, interval),
            )
            conn.execute(
                """UPDATE learning_memory SET due_at = ?, interval_days = ?, repetitions = ?,
                   lapses = lapses + ?, last_reviewed_at = ?, last_rating = ?, updated_at = ?
                   WHERE id = ?""",
                (due_at, interval, repetitions, 1 if payload.rating == "again" else 0,
                 reviewed_at, payload.rating, reviewed_at, item_id),
            )
            updated = conn.execute("SELECT * FROM learning_memory WHERE id = ?", (item_id,)).fetchone()
            history = conn.execute(
                "SELECT rating, reviewed_at, previous_due_at, next_due_at, interval_days FROM learning_memory_reviews WHERE item_id = ? ORDER BY reviewed_at DESC LIMIT 20",
                (item_id,),
            ).fetchall()
        return {"item": _item(updated), "review": dict(history[0]),
                "history": [dict(entry) for entry in history],
                "schedule_note": f"Next review in {interval} day(s) ({payload.rating})."}

    @router.get("/stats")
    def stats() -> dict[str, Any]:
        now = _stamp()
        with connect_database(Path(db_path)) as conn:
            totals = conn.execute(
                """SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN status = 'suspended' THEN 1 ELSE 0 END) AS suspended,
                   SUM(CASE WHEN status = 'active' AND due_at <= ? THEN 1 ELSE 0 END) AS due
                   FROM learning_memory""", (now,)
            ).fetchone()
            reviews = conn.execute("SELECT COUNT(*) AS n FROM learning_memory_reviews").fetchone()["n"]
        return {"total": totals["total"] or 0, "active": totals["active"] or 0,
                "suspended": totals["suspended"] or 0, "due": totals["due"] or 0,
                "reviews_completed": reviews,
                "note": "Activity counts only; they do not represent proficiency or learning gain."}

    return router
