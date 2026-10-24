from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prepped.main import create_app
from prepped.scenarios import ScenarioValidationError, load_scenario


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "scenarios" / "project-explanation.v1.json"


def test_health_endpoint_and_database_initialization(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "test.sqlite3"
    app = create_app(db_path=db_path, scenario_path=SCENARIO_PATH)

    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "application": "Prepped"}
    assert db_path.is_file()

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"sessions", "answers"}.issubset(tables)


def test_homepage_is_served() -> None:
    with TestClient(create_app(db_path=Path(":memory:"), scenario_path=SCENARIO_PATH)) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Prepped" in response.text
    assert "practice flow and feedback engine are not implemented yet" in response.text


def test_scenario_endpoint_returns_versioned_scenario(tmp_path: Path) -> None:
    with TestClient(create_app(db_path=tmp_path / "test.sqlite3", scenario_path=SCENARIO_PATH)) as client:
        response = client.get("/api/scenarios/project-explanation")

    assert response.status_code == 200
    scenario = response.json()
    assert scenario["id"] == "project-explanation"
    assert scenario["version"] == "1.0.0"
    assert len(scenario["questions"]) == 5
    assert {item["id"] for item in scenario["rubric"]} == {
        "clarity",
        "structure",
        "specificity",
        "follow_up_handling",
        "conciseness",
    }


def test_duplicate_question_ids_are_rejected(tmp_path: Path) -> None:
    scenario = {
        "id": "bad",
        "version": "1",
        "title": "Bad scenario",
        "description": "Invalid test fixture",
        "role": "Interviewer",
        "questions": [
            {"id": "same", "prompt": "First question?"},
            {"id": "same", "prompt": "Second question?"},
        ],
        "rubric": [{"id": "clarity", "label": "Clarity", "question": "Is it clear?"}],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(scenario), encoding="utf-8")

    with pytest.raises(ScenarioValidationError, match="Duplicate question id"):
        load_scenario(path)


def test_missing_scenario_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ScenarioValidationError, match="not found"):
        load_scenario(tmp_path / "missing.json")
