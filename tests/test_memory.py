from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from prepped.main import create_app


def client_for(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "prepped.sqlite3"))


def create_card(client: TestClient, **overrides):
    payload = {
        "item_type": "phrase",
        "front": "in the long run",
        "back": "Over a long period of time.",
        "source_type": "lesson",
        "source_id": "vocabulary-in-context",
        "source_title": "Vocabulary in context",
        "source_excerpt": "Use the phrase in a sentence.",
    }
    payload.update(overrides)
    return client.post("/api/memory/items", json=payload)


def test_memory_create_list_source_and_due_now(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        created = create_card(client)
        assert created.status_code == 201
        item = created.json()["item"]
        assert item["front"] == "in the long run"
        assert item["source_id"] == "vocabulary-in-context"
        assert item["status"] == "active"
        assert item["interval_days"] == 0
        assert client.get("/api/memory/items").json()["count"] == 1
        queue = client.get("/api/memory/review/queue").json()
        assert queue["count"] == 1
        assert queue["items"][0]["id"] == item["id"]


def test_memory_duplicate_detection_is_normalised_and_type_scoped(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        assert create_card(client).status_code == 201
        duplicate = create_card(client, front="  IN   THE LONG RUN ")
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["existing_id"]
        different_type = create_card(client, item_type="word", front="in the long run")
        assert different_type.status_code == 201


def test_memory_validation_and_update_preserve_source_and_schedule(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        created = create_card(client).json()["item"]
        assert create_card(client, front="  ").status_code == 422
        updated = client.put(f"/api/memory/items/{created['id']}", json={
            "front": "over time", "back": "As time passes."
        })
        assert updated.status_code == 200
        item = updated.json()["item"]
        assert item["front"] == "over time"
        assert item["source_id"] == "vocabulary-in-context"
        assert item["interval_days"] == 0
        assert client.put(f"/api/memory/items/{created['id']}", json={}).status_code == 422


def test_memory_review_scheduler_ratings_are_transparent_and_persist(tmp_path: Path) -> None:
    db = tmp_path / "prepped.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        item = create_card(client).json()["item"]
        first = client.post(f"/api/memory/items/{item['id']}/review", json={"rating": "good"})
        assert first.status_code == 200
        assert first.json()["item"]["interval_days"] == 1
        assert first.json()["review"]["rating"] == "good"
        assert client.get("/api/memory/review/queue").json()["count"] == 0

        second = client.post(f"/api/memory/items/{item['id']}/review", json={"rating": "easy"})
        assert second.status_code == 200
        assert second.json()["item"]["interval_days"] == 3
        assert second.json()["item"]["repetitions"] == 2

        third = client.post(f"/api/memory/items/{item['id']}/review", json={"rating": "again"})
        assert third.status_code == 200
        assert third.json()["item"]["interval_days"] == 1
        assert third.json()["item"]["repetitions"] == 0
        assert third.json()["item"]["lapses"] == 1
        assert third.json()["history"][0]["rating"] == "again"

        stats = client.get("/api/memory/stats").json()
        assert stats["total"] == 1
        assert stats["reviews_completed"] == 3

    with TestClient(create_app(db_path=db)) as restarted:
        saved = restarted.get(f"/api/memory/items/{item['id']}").json()["item"]
        assert saved["last_rating"] == "again"
        assert saved["lapses"] == 1


def test_memory_suspend_resume_and_delete_review_history_cascade(tmp_path: Path) -> None:
    db = tmp_path / "prepped.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        item = create_card(client).json()["item"]
        assert client.post(f"/api/memory/items/{item['id']}/review", json={"rating": "good"}).status_code == 200
        suspended = client.patch(f"/api/memory/items/{item['id']}/status?status=suspended")
        assert suspended.status_code == 200
        assert suspended.json()["item"]["status"] == "suspended"
        assert client.get("/api/memory/review/queue").json()["count"] == 0
        blocked = client.post(f"/api/memory/items/{item['id']}/review", json={"rating": "good"})
        assert blocked.status_code == 409
        assert client.patch(f"/api/memory/items/{item['id']}/status?status=active").json()["item"]["status"] == "active"
        assert client.delete(f"/api/memory/items/{item['id']}").status_code == 204
        assert client.get(f"/api/memory/items/{item['id']}").status_code == 404

    connection = sqlite3.connect(db)
    assert connection.execute("SELECT COUNT(*) FROM learning_memory_reviews").fetchone()[0] == 0
    connection.close()


def test_memory_rejects_invalid_rating_and_unknown_item(tmp_path: Path) -> None:
    with client_for(tmp_path) as client:
        assert client.post("/api/memory/items/missing/review", json={"rating": "perfect"}).status_code == 422
        assert client.post("/api/memory/items/missing/review", json={"rating": "good"}).status_code == 404
        assert client.patch("/api/memory/items/missing/status?status=active").status_code == 404


def test_memory_migration_preserves_existing_practice_and_learning_data(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite3"
    with TestClient(create_app(db_path=db)) as client:
        started = client.post("/api/learning/attempts", json={"lesson_id": "sentence-building"}).json()
        client.put("/api/profile", json={
            "primary_goal": "english_fluency", "confidence_level": "beginner"
        })
        item = create_card(client).json()["item"]
    with TestClient(create_app(db_path=db)) as client:
        assert client.get(f"/api/learning/attempts/{started['id']}").status_code == 200
        assert client.get("/api/profile").json()["profile"]["primary_goal"] == "english_fluency"
        assert client.get(f"/api/memory/items/{item['id']}").status_code == 200
