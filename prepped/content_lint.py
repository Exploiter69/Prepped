"""Cross-file curriculum and Career Studio quality checks for startup and CI."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from prepped.career import DEFAULT_STUDIOS_PATH, load_studios
from prepped.learning import DEFAULT_CURRICULUM_PATH, load_curriculum

class ContentBundleValidationError(ValueError):
    """Curriculum and Career Studio content do not form a coherent bundle."""

def validate_content_bundle(curriculum_path: Path = DEFAULT_CURRICULUM_PATH, studios_path: Path = DEFAULT_STUDIOS_PATH) -> dict[str, Any]:
    curriculum=load_curriculum(Path(curriculum_path))
    catalog=load_studios(Path(studios_path))
    skills={item["id"]:item for item in curriculum["skills"]}
    studios={item["id"]:item for item in catalog["studios"]}
    lesson_skill_ids={sid for lesson in curriculum["lessons"] for sid in lesson.get("skill_ids",[])}
    for studio in studios.values():
        for question in studio["questions"]:
            if any(sid not in skills for sid in question["skill_ids"]):
                raise ContentBundleValidationError(f"Studio {studio['id']} question {question['id']} references an unknown skill.")
    for sid,skill in skills.items():
        declared=set(skill.get("studio_ids",[]))
        actual={studio_id for studio_id,studio in studios.items() if sid in studio["skill_ids"]}
        if declared != actual:
            raise ContentBundleValidationError(f"Skill {sid} studio mapping does not match the Career Studio catalog.")
        if skill.get("status","active")=="active" and sid not in lesson_skill_ids and not actual:
            raise ContentBundleValidationError(f"Active skill {sid} is not taught by a lesson or Career Studio.")
    for track in curriculum["tracks"]:
        studio_ids=set(track.get("studio_ids",[]))
        if not studio_ids.issubset(studios):
            raise ContentBundleValidationError(f"Track {track['id']} references an unknown Career Studio.")
        for studio_id in studio_ids:
            missing=set(studios[studio_id]["skill_ids"])-set(track.get("skill_ids",[]))
            if missing:
                raise ContentBundleValidationError(f"Track {track['id']} omits skills from studio {studio_id}: {sorted(missing)}.")
    return {"curriculum_version":curriculum["schema_version"],"career_version":catalog["version"],
      "skills":len(skills),"tracks":len(curriculum["tracks"]),"units":len(curriculum["units"]),
      "lessons":len(curriculum["lessons"]),"exercises":sum(len(x["exercises"]) for x in curriculum["lessons"]),
      "studios":len(studios),"studio_questions":sum(len(x["questions"]) for x in studios.values()),
      "sources":len(curriculum["sources"])+len(catalog["sources"])}

def main() -> None:
    parser=argparse.ArgumentParser(description="Validate Prepped's versioned learning content.")
    parser.add_argument("--curriculum",type=Path,default=DEFAULT_CURRICULUM_PATH)
    parser.add_argument("--studios",type=Path,default=DEFAULT_STUDIOS_PATH)
    args=parser.parse_args()
    summary=validate_content_bundle(args.curriculum,args.studios)
    print("Prepped content validation passed")
    for key,value in summary.items(): print(f"{key}: {value}")

if __name__=="__main__": main()
