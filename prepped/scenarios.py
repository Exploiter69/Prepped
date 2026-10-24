"""Load and validate versioned JSON scenario definitions."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIO_PATH = ROOT / "scenarios" / "project-explanation.v1.json"


class ScenarioValidationError(ValueError):
    """Raised when a scenario definition is missing or invalid."""


def load_scenario(path: Path = DEFAULT_SCENARIO_PATH) -> dict[str, Any]:
    """Read a scenario JSON file and validate its minimal contract."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ScenarioValidationError("Scenario file was not found.") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioValidationError("Scenario file is not valid JSON.") from exc

    if not isinstance(data, dict):
        raise ScenarioValidationError("Scenario root must be a JSON object.")

    for field in ("id", "version", "title", "description", "role", "questions", "rubric"):
        if field not in data:
            raise ScenarioValidationError(f"Missing required field: {field}")

    for field in ("id", "version", "title", "description", "role"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ScenarioValidationError(f"Field '{field}' must be a non-empty string.")

    questions = data["questions"]
    if not isinstance(questions, list) or not questions:
        raise ScenarioValidationError("Scenario must contain at least one question.")

    question_ids: set[str] = set()
    for question in questions:
        if not isinstance(question, dict):
            raise ScenarioValidationError("Each question must be an object.")
        question_id = question.get("id")
        prompt = question.get("prompt")
        if not isinstance(question_id, str) or not question_id.strip():
            raise ScenarioValidationError("Each question needs a non-empty id.")
        if question_id in question_ids:
            raise ScenarioValidationError(f"Duplicate question id: {question_id}")
        question_ids.add(question_id)
        if not isinstance(prompt, str) or not prompt.strip():
            raise ScenarioValidationError(f"Question '{question_id}' needs a prompt.")

    rubric = data["rubric"]
    if not isinstance(rubric, list) or not rubric:
        raise ScenarioValidationError("Scenario must contain at least one rubric criterion.")

    criterion_ids: set[str] = set()
    for criterion in rubric:
        if not isinstance(criterion, dict):
            raise ScenarioValidationError("Each rubric criterion must be an object.")
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            raise ScenarioValidationError("Each rubric criterion needs a non-empty id.")
        if criterion_id in criterion_ids:
            raise ScenarioValidationError(f"Duplicate rubric criterion id: {criterion_id}")
        criterion_ids.add(criterion_id)
        if not isinstance(criterion.get("label"), str) or not criterion["label"].strip():
            raise ScenarioValidationError(f"Criterion '{criterion_id}' needs a label.")

    return data
