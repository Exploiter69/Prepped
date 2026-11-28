from __future__ import annotations

import json
from pathlib import Path

import pytest

from prepped.content_lint import ContentBundleValidationError, validate_content_bundle
from prepped.learning import load_curriculum


def test_content_bundle_has_complete_skill_and_studio_coverage() -> None:
    summary = validate_content_bundle()
    assert summary == {
        "curriculum_version": "1.2.0",
        "career_version": "1.3.0",
        "skills": 14,
        "tracks": 4,
        "units": 14,
        "lessons": 46,
        "exercises": 155,
        "studios": 3,
        "studio_questions": 12,
        "sources": 18,
    }


def test_content_bundle_rejects_inconsistent_skill_to_studio_mapping(tmp_path: Path) -> None:
    curriculum = load_curriculum()
    skill = next(item for item in curriculum["skills"] if item["id"] == "communication.project-summary")
    skill["studio_ids"] = []
    curriculum_path = tmp_path / "curriculum.json"
    curriculum_path.write_text(json.dumps(curriculum), encoding="utf-8")

    with pytest.raises(ContentBundleValidationError, match="studio mapping"):
        validate_content_bundle(curriculum_path)
