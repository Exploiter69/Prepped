"""Deterministic, evidence-linked formative feedback.

This module reports explainable text signals, not a person's ability or placement
readiness. Each prompt has its own checks; a detected phrase is never proof that
the answer is correct or that a real-world outcome has been achieved.
"""
from __future__ import annotations

import re
from typing import Any


# These are deliberately small, inspectable phrase lists, not a language model.
# A match is only a prompt for learner review, never a quality verdict.
OVERVIEW_PROBLEM = (
    "problem", "needed to", "wanted to address", "because", "challenge",
    "students missed", "students had to", "difficult to", "hard to",
)
OVERVIEW_BENEFIT = (
    "students", "users", "learners", "helps", "benefit", "for people",
    "makes it easier", "so that", "in one place",
)
OVERVIEW_FEATURES = (
    "posts", "replies", "polls", "voting", "directory", "notices", "feed",
    "search", "dashboard", "api", "database", "endpoint", "test", "interface",
)
CONTRIBUTION_ACTIONS = (
    "i built", "i implemented", "i wrote", "i developed", "i designed",
    "i created", "i worked on", "i was responsible", "my contribution",
    "my role", "i contributed", "i added", "i maintained",
)
ARTIFACT_DETAILS = (
    "api", "endpoint", "database", "sqlite", "fastapi", "python", "javascript",
    "test", "migration", "worker", "interface", "posts", "replies", "polls",
    "directory", "authentication", "validation", "deployment",
)
DECISION_CHOICES = (
    "i chose", "i decided", "i used", "i selected", "i went with",
    "the decision", "i kept", "i avoided",
)
ALTERNATIVES_CONSTRAINTS = (
    "considered", "alternative", "instead", "trade-off", "tradeoff",
    "constraint", "cost", "complexity", "compared with", "rather than",
    "would add", "because",
)
TEST_EVIDENCE = (
    "tested", "tests passed", "test passed", "verified", "checked",
    "ran the tests", "manual test", "observed", "measured", "measurement",
    "logs showed", "successfully", "working locally", "request returned",
)
LIMITATION_EVIDENCE = (
    "have not measured", "haven't measured", "not measured", "not yet measured",
    "have not tested with", "haven't tested with", "not tested with",
    "have not collected", "haven't collected", "no user data",
    "not collected", "don't know yet", "do not know yet",
)
REFLECTION_IMPROVEMENT = (
    "next", "improve", "improvement", "would change", "would add",
    "prioritise", "prioritize", "fix", "test with users", "user feedback",
)
REFLECTION_LEARNING = (
    "i learned", "i learnt", "i learned", "taught me", "i realised",
    "i realized", "i discovered", "i now understand",
)
STRUCTURE_MARKERS = (
    "first", "then", "next", "finally", "as a result", "because", "so that",
)


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
    """Match phrases without treating a short token as part of a longer word."""
    lowered = text.casefold()
    for marker in markers:
        pattern = rf"(?<!\w){re.escape(marker.casefold())}(?!\w)"
        if re.search(pattern, lowered):
            return True
    return False


def _repeated_sentence_count(text: str) -> int:
    """Count exact repeated sentences, ignoring case and surrounding punctuation."""
    sentences = re.split(r"(?<=[.!?])\\s+", text.strip())
    seen: set[str] = set()
    repeated: set[str] = set()
    for sentence in sentences:
        normalized = re.sub(r"[^\\w' -]", "", sentence.casefold()).strip()
        if len(_words(normalized)) < 4:
            continue
        if normalized in seen:
            repeated.add(normalized)
        seen.add(normalized)
    return len(repeated)


def _question_signal(question_id: str, answer: str) -> tuple[bool, str]:
    """Return whether a prompt-specific signal exists and what may be missing."""
    if question_id == "project_overview":
        has_problem = _contains_marker(answer, OVERVIEW_PROBLEM)
        has_benefit = _contains_marker(answer, OVERVIEW_BENEFIT)
        has_feature = _contains_marker(answer, OVERVIEW_FEATURES)
        if has_problem and has_benefit and has_feature:
            return True, "Keep the example, and make sure it names the problem, a real feature, and who benefits."
        missing = []
        if not has_problem:
            missing.append("the problem you were addressing")
        if not has_benefit:
            missing.append("who benefits or how")
        if not has_feature:
            missing.append("one concrete feature or example")
        return False, "Add " + ", ".join(missing) + " if you can support it with your actual work."
    if question_id == "personal_contribution":
        has_action = _contains_marker(answer, CONTRIBUTION_ACTIONS)
        has_detail = _contains_marker(answer, ARTIFACT_DETAILS)
        if has_action and has_detail:
            return True, "Keep the specific contribution and be ready to explain what you personally implemented."
        if not has_action:
            return False, "State what you personally built, changed, tested, or maintained; separate your work from the team's."
        return False, "Name one concrete artifact you worked on, such as an endpoint, data model, test, or interface."
    if question_id == "design_decision":
        has_choice = _contains_marker(answer, DECISION_CHOICES)
        has_alternative = _contains_marker(answer, ALTERNATIVES_CONSTRAINTS)
        if has_choice and has_alternative:
            return True, "Keep both the decision and the alternative or constraint, then explain the trade-off."
        if not has_choice:
            return False, "State the decision you actually made before explaining the reasoning."
        return False, "Name an alternative or constraint you genuinely considered, and explain why it mattered."
    if question_id == "evidence_and_result":
        has_test = _contains_marker(answer, TEST_EVIDENCE)
        has_limit = _contains_marker(answer, LIMITATION_EVIDENCE)
        if has_test and has_limit:
            return True, "Separate what you directly tested or observed from what remains unmeasured."
        if not has_test:
            return False, "Give a real check or observed result (for example, a test you ran); feature existence alone is not a test result."
        return False, "State what you have not measured or verified yet; do not imply user impact without evidence."
    if question_id == "reflection":
        has_improvement = _contains_marker(answer, REFLECTION_IMPROVEMENT)
        has_learning = _contains_marker(answer, REFLECTION_LEARNING)
        if has_improvement and has_learning:
            return True, "Keep one specific next improvement and one lesson learned from the work."
        if not has_improvement:
            return False, "Name one concrete next improvement and why you would prioritise it."
        return False, "State one lesson you personally learned, ideally tied to a decision or mistake."
    return (
        _contains_marker(answer, ARTIFACT_DETAILS),
        "Add a concrete detail you can explain, if you have one; do not invent evidence.",
    )


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
        question_id = question["id"]
        answer = by_question.get(question_id, "").strip()
        count = len(_words(answer))
        if not answer:
            status = "not_enough_evidence"
            message = "No answer was provided, so there is not enough evidence to comment on this response."
            next_action = "Try answering in two or three sentences, or use Skip if you want to move on."
        elif count < 8:
            status = "try_next"
            message = "This response is very brief. It may leave the interviewer without enough context."
            next_action = "Add the key detail this question asks for, using only what you actually did or observed."
        else:
            signal_found, next_action = _question_signal(question_id, answer)
            if signal_found:
                status = "evidence_found"
                message = "The answer includes phrase signals relevant to this prompt. Review the excerpt to confirm they describe your actual work."
            else:
                status = "try_next"
                message = "The checklist could not find all of the expected signals for this prompt. That does not prove the answer is wrong."
        question_feedback.append({
            "question_id": question_id,
            "prompt": question["prompt"],
            "status": status,
            "word_count": count,
            "evidence": _evidence_excerpt(answer),
            "message": message,
            "next_action": next_action,
        })

    rubric_feedback: list[dict[str, Any]] = []
    overview = by_question.get("project_overview", "").strip()
    for criterion in rubric:
        criterion_id = criterion["id"]
        if not combined:
            status = "not_enough_evidence"
            message = "No non-empty answers were provided; this checklist item cannot be reviewed."
            evidence = None
            next_action = "Try one question with a concrete example before interpreting this item."
        elif criterion_id == "clarity":
            count = len(_words(overview))
            has_problem = _contains_marker(overview, OVERVIEW_PROBLEM)
            has_benefit = _contains_marker(overview, OVERVIEW_BENEFIT)
            status = "evidence_found" if count >= 12 and has_problem and has_benefit else "try_next"
            evidence = _evidence_excerpt(overview)
            message = (
                "The overview contains phrase signals for a problem and beneficiary; this cannot confirm that a listener understood it."
                if status == "evidence_found"
                else "The checklist could not find both a problem signal and a beneficiary signal in the overview."
            )
            next_action = "Introduce the problem, then say who it affects and how your project helps."
        elif criterion_id == "structure":
            has_problem = _contains_marker(overview, OVERVIEW_PROBLEM)
            has_solution = _contains_marker(overview, OVERVIEW_FEATURES)
            has_benefit = _contains_marker(overview, OVERVIEW_BENEFIT)
            status = "evidence_found" if has_problem and has_solution and has_benefit else "try_next"
            evidence = _evidence_excerpt(overview)
            message = (
                "The overview contains phrase signals for a problem, solution detail, and beneficiary; their logical order is not verified."
                if status == "evidence_found"
                else "One or more expected overview elements were not recognised by the checklist."
            )
            next_action = "Try this order: problem → your approach or feature → who benefits or current evidence."
        elif criterion_id == "specificity":
            matches = [
                (question, by_question.get(question["id"], "").strip())
                for question in questions
                if by_question.get(question["id"], "").strip()
                and _question_signal(question["id"], by_question[question["id"]].strip())[0]
            ]
            evidence = _evidence_excerpt(matches[0][1]) if matches else _evidence_excerpt(combined)
            status = "evidence_found" if matches else "try_next"
            message = (
                "At least one answer contains prompt-specific phrase signals. Check that the detail is accurate and supports the point."
                if matches
                else "No prompt-specific detail pattern was recognised. The heuristic may miss valid evidence."
            )
            next_action = "Use one real implementation detail, decision, test, or observed result that you can explain."
        elif criterion_id == "follow_up_handling":
            answered = sum(bool(by_question.get(question["id"], "").strip()) for question in questions)
            status = "evidence_found" if answered == len(questions) else "try_next"
            evidence = f"{answered} of {len(questions)} questions have non-empty answers."
            message = "This counts answered prompts only; it cannot determine whether an answer is relevant." if answered == len(questions) else "Some prompts were skipped or left blank."
            next_action = "Make the first sentence directly answer the question before adding context."
        elif criterion_id == "conciseness":
            answer_details = [
                (question, text, len(_words(text)), _repeated_sentence_count(text))
                for question in questions
                if (text := by_question.get(question["id"], "").strip())
            ]
            repeated_answers = [item for item in answer_details if item[3] > 0]
            very_long_answers = [item for item in answer_details if item[2] > 180]
            flagged = repeated_answers or very_long_answers
            evidence = _evidence_excerpt(flagged[0][1]) if flagged else _evidence_excerpt(combined)
            if repeated_answers:
                _, _, count, repeated_count = repeated_answers[0]
                status = "try_next"
                message = (
                    f"One answer contains {repeated_count} repeated full sentence(s). "
                    "This exact-text check can miss repeated ideas phrased differently."
                )
                next_action = "Check whether the repeated sentence adds anything new; remove it only if it repeats an earlier point."
            elif very_long_answers:
                _, _, count, _ = very_long_answers[0]
                seconds = round(count / 130 * 60)
                status = "try_next"
                message = (
                    f"One answer has {count} words, roughly {seconds} seconds at an illustrative "
                    "130 words per minute. Word count cannot determine whether the spoken answer feels too long."
                )
                next_action = "Try saying the answer aloud; keep the details that directly answer the prompt and remove only what feels unnecessary."
            else:
                status = "evidence_found"
                if answer_details:
                    longest = max(answer_details, key=lambda item: item[2])
                    seconds = round(longest[2] / 130 * 60)
                    message = (
                        f"The longest answer has {longest[2]} words, roughly {seconds} seconds at an illustrative "
                        "130 words per minute. No exact repeated full sentence was detected; repeated ideas may still be present."
                    )
                else:
                    message = "No non-empty answers were available to review for conciseness."
                next_action = "Read each answer aloud once. Keep the details needed to answer the prompt; this checklist cannot judge natural spoken delivery."
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
            "Phrase patterns can miss good answers and can also match weak or inaccurate answers.",
            "No overall score, personality judgement, or placement prediction is produced.",
            "Only submitted text is analysed; speaking, pronunciation, listener understanding, and real-world outcomes are not measured.",
        ],
    }
