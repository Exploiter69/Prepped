"""Deterministic, evidence-linked formative feedback.

This module does not grade a person's ability or predict placement outcomes.
It only reports simple, explainable signals found in the submitted text.
"""
from __future__ import annotations

import re
from typing import Any


CONCRETE_MARKERS = (
    "for example", "for instance", "because", "built", "implemented", "tested",
    "measured", "users", "user", "database", "api", "python", "javascript",
    "fastapi", "sqlite", "react", "latency", "seconds", "percent", "%",
)
STRUCTURE_MARKERS = ("first", "then", "next", "finally", "because", "so that", "as a result")


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)


def _evidence_excerpt(text: str, limit: int = 180) -> str | None:
    """Return an exact, bounded excerpt from the user's own answer."""
    clean = text.strip()
    if not clean:
        return None
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rsplit(" ", 1)[0] + "…"


def _contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in markers)


def build_feedback(session: dict[str, Any], answers: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an explainable feedback report without an overall score."""
    scenario = session.get("scenario") or {}
    questions = scenario.get("questions", [])
    rubric = session.get("rubric") or scenario.get("rubric", [])
    by_question = {answer["question_id"]: answer["answer_text"] for answer in answers}
    nonempty = [text.strip() for text in by_question.values() if text.strip()]
    combined = "\n".join(nonempty)
    total_words = sum(len(_words(text)) for text in nonempty)

    question_feedback: list[dict[str, Any]] = []
    for question in questions:
        answer = by_question.get(question["id"], "").strip()
        count = len(_words(answer))
        if not answer:
            status = "not_enough_evidence"
            message = "No answer was provided, so there is not enough evidence to comment on this response."
            next_action = "Try answering in two or three sentences, or use Skip if you want to move on."
        elif count < 8:
            status = "try_next"
            message = "This response is very brief. It may leave the interviewer without enough context."
            next_action = "Add the specific situation, what you did, and one detail that supports the point."
        elif _contains_marker(answer, CONCRETE_MARKERS):
            status = "evidence_found"
            message = "This answer contains at least one concrete-detail signal. Check that it directly supports your main point."
            next_action = "Keep the detail and explain why it matters to the problem or decision."
        else:
            status = "try_next"
            message = "The text does not contain a clear concrete-detail signal recognised by this simple checklist."
            next_action = "Add a specific example, tool, constraint, test, measurement, or result if you have one. Do not invent evidence."
        question_feedback.append({
            "question_id": question["id"],
            "prompt": question["prompt"],
            "status": status,
            "word_count": count,
            "evidence": _evidence_excerpt(answer),
            "message": message,
            "next_action": next_action,
        })

    rubric_feedback: list[dict[str, Any]] = []
    for criterion in rubric:
        criterion_id = criterion["id"]
        if not combined:
            status = "not_enough_evidence"
            message = "No non-empty answers were provided; this checklist item cannot be assessed."
            evidence = None
            next_action = "Try one question with a concrete example before interpreting this item."
        elif criterion_id == "clarity":
            answer = by_question.get("project_overview", "").strip()
            count = len(_words(answer))
            status = "evidence_found" if count >= 12 else "not_enough_evidence"
            evidence = _evidence_excerpt(answer)
            message = (
                "The project overview has enough text for a first clarity review; this does not prove that a listener understood it."
                if status == "evidence_found"
                else "There is not enough text in the project overview to review clarity."
            )
            next_action = "State the problem first, then the solution and who benefits."
        elif criterion_id == "structure":
            answer = by_question.get("project_overview", "").strip()
            status = "evidence_found" if _contains_marker(answer, STRUCTURE_MARKERS) else "try_next"
            evidence = _evidence_excerpt(answer)
            message = (
                "The overview contains a linking or sequencing phrase."
                if status == "evidence_found"
                else "The overview does not contain a sequencing/linking signal recognised by this checklist."
            )
            next_action = "Try a simple order: problem → your approach → result or current evidence."
        elif criterion_id == "specificity":
            matches = [text for text in nonempty if _contains_marker(text, CONCRETE_MARKERS)]
            evidence = _evidence_excerpt(matches[0]) if matches else _evidence_excerpt(combined)
            status = "evidence_found" if matches else "try_next"
            message = (
                "At least one answer contains a concrete-detail signal recognised by this checklist."
                if matches
                else "No recognised concrete-detail signal was found. The heuristic may miss valid technical details."
            )
            next_action = "Use a real example, implementation detail, constraint, test, or result that you can explain."
        elif criterion_id == "follow_up_handling":
            answered = sum(bool(by_question.get(question["id"], "").strip()) for question in questions)
            status = "evidence_found" if answered == len(questions) else "try_next"
            evidence = f"{answered} of {len(questions)} questions have non-empty answers."
            message = "This counts answered prompts only; it cannot determine semantic relevance." if answered == len(questions) else "Some prompts were skipped or left blank."
            next_action = "Make the first sentence directly answer the question before adding context."
        elif criterion_id == "conciseness":
            long_answers = [text for text in nonempty if len(_words(text)) > 120]
            evidence = _evidence_excerpt(long_answers[0]) if long_answers else _evidence_excerpt(combined)
            status = "try_next" if long_answers else ("evidence_found" if total_words else "not_enough_evidence")
            message = (
                "At least one response is over 120 words; consider trimming it. Length alone does not establish repetition."
                if long_answers
                else f"The non-empty answers contain {total_words} words in total; this checklist cannot judge spoken delivery."
            )
            next_action = "Lead with the answer, keep only relevant context, and finish with the evidence or takeaway."
        else:
            status = "not_enough_evidence"
            evidence = _evidence_excerpt(combined)
            message = "No deterministic rule is configured for this rubric item yet."
            next_action = "Review the rubric question and use your own judgement."
        rubric_feedback.append({
            "criterion_id": criterion_id,
            "label": criterion["label"],
            "question": criterion.get("question", ""),
            "status": status,
            "message": message,
            "evidence": evidence,
            "next_action": next_action,
        })

    return {
        "session_id": session["id"],
        "scenario_id": session["scenario_id"],
        "scenario_version": session["scenario_version"],
        "attempt_number": session["attempt_number"],
        "completed_at": session.get("completed_at"),
        "answered_questions": sum(bool(by_question.get(q["id"], "").strip()) for q in questions),
        "total_questions": len(questions),
        "total_words": total_words,
        "question_feedback": question_feedback,
        "rubric_feedback": rubric_feedback,
        "limitations": [
            "This is a transparent text heuristic, not an AI interviewer or validated assessment.",
            "Keyword and length signals can miss good answers and can also flag weak ones.",
            "No overall score, personality judgement, or placement prediction is produced.",
            "Only your submitted text is analysed; speaking, pronunciation, and listener understanding are not measured.",
        ],
    }
