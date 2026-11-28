"""Career preparation extensions (Pack C):
- C1: Structured Project Explanation Studio (Problem/Approach/Implementation/Decisions/Outcome/Learning)
- C2: Local deterministic Resume & Project topic extraction and question generation
- C3 & C4: Timed Mock Interview sessions with grounded debriefs
- C5: Low-friction 5-minute Interview Warm-up
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from prepped.database import connect_database
from prepped.speaking_analytics import analyze_transcript, summarize_session_delivery

CAREER_PREP_TABLES = """
CREATE TABLE IF NOT EXISTS learner_projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 140),
    problem TEXT NOT NULL DEFAULT '',
    approach TEXT NOT NULL DEFAULT '',
    implementation TEXT NOT NULL DEFAULT '',
    decisions_tradeoffs TEXT NOT NULL DEFAULT '',
    outcome TEXT NOT NULL DEFAULT '',
    learning TEXT NOT NULL DEFAULT '',
    tech_stack TEXT NOT NULL DEFAULT '',
    personal_role TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    source_kind TEXT NOT NULL DEFAULT 'project' CHECK (source_kind IN ('project', 'resume')),
    generated_questions_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learner_projects_updated ON learner_projects(updated_at DESC);

CREATE TABLE IF NOT EXISTS mock_interviews (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('timed_mock', 'warmup', 'project_studio', 'resume_prep')),
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 160),
    time_limit_seconds INTEGER CHECK (time_limit_seconds IS NULL OR time_limit_seconds BETWEEN 60 AND 3600),
    elapsed_seconds INTEGER NOT NULL DEFAULT 0 CHECK (elapsed_seconds >= 0),
    status TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'cancelled')),
    questions_json TEXT NOT NULL DEFAULT '[]',
    responses_json TEXT NOT NULL DEFAULT '[]',
    project_id TEXT REFERENCES learner_projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_mock_interviews_created ON mock_interviews(created_at DESC);
"""

KNOWN_TECH_TERMS = (
    "python", "c++", "java", "javascript", "typescript", "sql", "sqlite", "postgresql",
    "mysql", "mongodb", "redis", "fastapi", "django", "flask", "node.js", "express",
    "react", "next.js", "html", "css", "docker", "kubernetes", "linux", "git", "aws",
    "gcp", "cloudflare", "pytorch", "tensorflow", "opencv", "scikit-learn", "rest api",
    "graphql", "websocket", "ci/cd", "pytest", "playwright", "rust", "go", "c",
)

WARMUP_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "warmup_intro",
        "topic": "Introduction",
        "prompt": "Introduce yourself in 45 seconds: who you are, what you are studying, and one area you enjoy building in.",
        "tip": "Keep it to three clean beats: background, focus area, and one project highlight.",
        "suggested_seconds": 45,
    },
    {
        "id": "warmup_studies",
        "topic": "Current studies",
        "prompt": "Which subject or hands-on coursework has shaped how you think about engineering, and why?",
        "tip": "Name one concrete concept and how you applied it outside a textbook.",
        "suggested_seconds": 45,
    },
    {
        "id": "warmup_project",
        "topic": "Project snapshot",
        "prompt": "In three sentences, explain one project you worked on and your exact contribution.",
        "tip": "Use Problem -> Your Role -> Result.",
        "suggested_seconds": 60,
    },
    {
        "id": "warmup_common",
        "topic": "Common HR question",
        "prompt": "Tell me about a mistake or bug that slowed you down and how you handled it.",
        "tip": "Focus on how you diagnosed it and what habit you changed afterward.",
        "suggested_seconds": 60,
    },
]

FLUENCY_432_PROMPTS: tuple[str, ...] = (
    "Explain your strongest college or personal project: the problem it solves, what you personally built, and one design trade-off.",
    "Introduce yourself using Present -> Past -> Future: your current focus, two real things you built or learned, and the kind of role you want next.",
    "Walk through a real technical bug you diagnosed: the symptom, root cause, fix, and how you verified it.",
)


def build_fluency_432_rounds(topic_prompt: str | None = None) -> list[dict[str, Any]]:
    """Build a 3-round compressed-repetition drill (Nation 1989; de Jong & Perfetti 2011)."""
    prompt = (topic_prompt or FLUENCY_432_PROMPTS[0]).strip()
    return [
        {
            "id": "fluency_432_r1",
            "topic": "Round 1 of 3 · 90s Explore (4/3/2 Method)",
            "prompt": prompt,
            "tip": "Round 1 (90s): Focus on getting your full idea out cleanly. Do not stop for minor grammar slips.",
            "suggested_seconds": 90,
        },
        {
            "id": "fluency_432_r2",
            "topic": "Round 2 of 3 · 60s Tighten (Same Topic)",
            "prompt": prompt,
            "tip": "Round 2 (60s): Repeat the EXACT SAME explanation, cutting filler words and tightening long sentences.",
            "suggested_seconds": 60,
        },
        {
            "id": "fluency_432_r3",
            "topic": "Round 3 of 3 · 45s Crisp Delivery (Same Topic)",
            "prompt": prompt,
            "tip": "Round 3 (45s): Deliver the sharpest, smoothest version of the same points with calm pauses between sentences.",
            "suggested_seconds": 45,
        },
    ]


MOCK_QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "project": [
        {"id": "mock_proj_1", "topic": "Project overview", "prompt": "Walk me through your strongest project: what problem did it solve and who was it for?", "tip": "Start with one clear sentence on the problem before listing tech."},
        {"id": "mock_proj_2", "topic": "Personal ownership", "prompt": "What part of the project did you personally design, code, or test?", "tip": "Use 'I built / implemented / tested' rather than only 'we'."},
        {"id": "mock_proj_3", "topic": "Trade-off", "prompt": "What technical trade-off or alternative did you weigh, and why did you choose your current design?", "tip": "Name the alternative you rejected and the constraint that drove your choice."},
        {"id": "mock_proj_4", "topic": "Verification", "prompt": "How did you verify that your implementation worked, and what edge case surprised you?", "tip": "Cite actual tests, logs, or observations without inventing metrics."},
        {"id": "mock_proj_5", "topic": "Iteration", "prompt": "If you had two more weeks on this project, what would you improve first and why?", "tip": "Prioritise one high-impact limitation."},
        {"id": "mock_proj_6", "topic": "Data flow", "prompt": "Trace one core user action in your project from input to storage and back to the UI.", "tip": "Explain three layers cleanly: client request, backend validation/logic, and persistence."},
        {"id": "mock_proj_7", "topic": "Failure mode", "prompt": "What is the single most likely failure point if 50 users used your project concurrently?", "tip": "Be honest about locks, memory, or rate limits and state how you would scale it."},
        {"id": "mock_proj_8", "topic": "Security & privacy", "prompt": "What security or input-validation checks did you build into your project?", "tip": "Mention concrete bounds like schema validation, file permissions, or safe DOM rendering."},
        {"id": "mock_proj_9", "topic": "Debugging story", "prompt": "Tell me about the trickiest bug you hit while building this project and how you isolated it.", "tip": "Follow Symptom -> Root Cause -> Fix -> Regression check."},
        {"id": "mock_proj_10", "topic": "Non-technical pitch", "prompt": "Explain what your project does in 30 seconds to someone who does not write code.", "tip": "Skip jargon and focus on user problem and everyday outcome."},
    ],
    "hr": [
        {"id": "mock_hr_1", "topic": "Self-introduction", "prompt": "Tell me about yourself and what kind of engineering role you are preparing for.", "tip": "Use Present -> Past proof -> Future role alignment."},
        {"id": "mock_hr_2", "topic": "Teamwork", "prompt": "Describe a time you disagreed with a teammate on how to approach a task. How did you resolve it?", "tip": "Stay constructive and explain the shared criteria you used."},
        {"id": "mock_hr_3", "topic": "Pressure", "prompt": "Tell me about a deadline where you had to cut scope or reprioritise. What did you keep and what did you defer?", "tip": "Show clear reasoning behind your priority order."},
        {"id": "mock_hr_4", "topic": "Feedback", "prompt": "Share a piece of critical feedback you received on your work and how you acted on it.", "tip": "Name the feedback plainly and the concrete change you made."},
        {"id": "mock_hr_5", "topic": "Motivation", "prompt": "What kind of engineering problems do you want to work on in your first year after graduation?", "tip": "Be specific rather than generic."},
        {"id": "mock_hr_6", "topic": "Real weakness", "prompt": "What is one genuine skill or habit you are actively working to improve right now?", "tip": "Pick a real, non-cliché habit and describe the concrete system you use to improve it."},
        {"id": "mock_hr_7", "topic": "Ownership of mistake", "prompt": "Tell me about a mistake you made on a project or lab task and how you fixed it.", "tip": "Own your part without blaming others and state what habit changed afterward."},
        {"id": "mock_hr_8", "topic": "Learning fast", "prompt": "Describe a time you had to learn an unfamiliar tool or codebase quickly to finish a task.", "tip": "Explain how you broke the learning down into small working tests."},
        {"id": "mock_hr_9", "topic": "Handling ambiguity", "prompt": "Tell me about a time requirements were unclear. How did you clarify what to build?", "tip": "Show how you asked targeted questions and confirmed scope early."},
        {"id": "mock_hr_10", "topic": "Closing questions", "prompt": "Imagine we are at the end of a real interview: what two questions would you ask the panel?", "tip": "Ask one engineering-craft question and one team/onboarding question."},
    ],
    "technical": [
        {"id": "mock_tech_1", "topic": "Debugging", "prompt": "Walk me through a tricky bug you diagnosed recently. What clues did you check first?", "tip": "Explain your hypothesis-and-check sequence step by step."},
        {"id": "mock_tech_2", "topic": "Data structures", "prompt": "When would you choose a hash map over a sorted array or balanced tree? Give a concrete example.", "tip": "Compare lookup time, ordering, and memory overhead."},
        {"id": "mock_tech_3", "topic": "Databases", "prompt": "Why do indexes speed up reads, and what trade-off do they introduce for writes?", "tip": "Mention lookup cost versus extra storage and write updates."},
        {"id": "mock_tech_4", "topic": "API design", "prompt": "How would you design a reliable HTTP endpoint that handles invalid input and slow downstream work?", "tip": "Cover validation, status codes, timeouts, and clear errors."},
        {"id": "mock_tech_5", "topic": "Testing", "prompt": "What is the difference between a unit test and an integration test, and when do you reach for each?", "tip": "Connect it to a real module you have written."},
        {"id": "mock_tech_6", "topic": "Arrays vs linked lists", "prompt": "Why do dynamic arrays often outperform linked lists in practice even when linked lists have O(1) insertion?", "tip": "Mention contiguous memory, CPU cache locality, and pointer overhead."},
        {"id": "mock_tech_7", "topic": "Transactions", "prompt": "What problem does a database transaction solve, and what happens during a rollback?", "tip": "Give a concrete multi-step write example."},
        {"id": "mock_tech_8", "topic": "OS processes & threads", "prompt": "How do processes and threads differ in memory sharing and failure isolation?", "tip": "Contrast isolated address space versus shared heap and race-condition risks."},
        {"id": "mock_tech_9", "topic": "Networking & HTTP", "prompt": "What happens at a high level between typing a URL in a browser and receiving an HTTP response?", "tip": "Walk cleanly through DNS, TCP/TLS handshake, HTTP request, and server response."},
        {"id": "mock_tech_10", "topic": "Unknown concept recovery", "prompt": "If I ask about a distributed-systems tool you haven't used yet, how do you reason through it honestly?", "tip": "Use Honest boundary -> Closest known fundamental -> How you'd verify."},
    ],
    "workplace": [
        {"id": "mock_work_1", "topic": "Daily standup", "prompt": "Give a 45-second daily standup update for your current project: Done, Next, and any Blocker.", "tip": "Skip long backstory; state outcomes and specific blockers clearly."},
        {"id": "mock_work_2", "topic": "Code review", "prompt": "A teammate's pull request skips validation on user input. How do you explain the risk constructively?", "tip": "Focus on the code and failure risk, never the person."},
        {"id": "mock_work_3", "topic": "Risk escalation", "prompt": "Two days before a demo, a secondary feature is unstable. How do you update your mentor with options?", "tip": "Use Status -> Risk -> Two Options -> Recommendation."},
        {"id": "mock_work_4", "topic": "BLUF briefing", "prompt": "Summarise a recent technical fix in 20 seconds using Bottom Line Up Front.", "tip": "Lead with the outcome first, then one sentence of technical cause."},
        {"id": "mock_work_5", "topic": "Requirements clarification", "prompt": "A mentor asks you to 'make the search page faster' with no details. What clarifying questions do you ask?", "tip": "Narrow down data size, query bottleneck, and perceived latency."},
        {"id": "mock_work_6", "topic": "Receiving critique", "prompt": "A senior engineer points out a race condition in your code during review. How do you respond?", "tip": "Acknowledge the catch objectively and state your fix plus regression test."},
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_career_prep_database(db_path: Path) -> None:
    with connect_database(Path(db_path)) as conn:
        conn.executescript(CAREER_PREP_TABLES)


def build_project_questions(project: dict[str, Any]) -> list[dict[str, Any]]:
    title = project.get("title") or "your project"
    stack = project.get("tech_stack") or ""
    role = project.get("personal_role") or ""
    return [
        {
            "id": "proj_problem",
            "topic": "Problem & Purpose",
            "prompt": f"In under a minute, what problem does {title} solve, and why did it matter?",
            "tip": f"Anchor in your notes: {(project.get('problem') or 'State the user pain clearly.')[:120]}",
        },
        {
            "id": "proj_role",
            "topic": "Personal Contribution",
            "prompt": f"What was your specific role in {title}" + (f" ({role})" if role else "") + ", and what did you personally build?",
            "tip": "Lead with 'I built / implemented / tested' and name concrete modules.",
        },
        {
            "id": "proj_approach",
            "topic": "Architecture & Implementation",
            "prompt": f"Walk me through how {title} works under the hood" + (f" using {stack}" if stack else "") + ".",
            "tip": "Explain the main flow in 3 steps: input, core logic/storage, and output.",
        },
        {
            "id": "proj_tradeoff",
            "topic": "Decisions & Trade-offs",
            "prompt": f"What key technical decision or trade-off did you make in {title}, and what alternative did you set aside?",
            "tip": f"Reference your trade-off note: {(project.get('decisions_tradeoffs') or 'Explain the constraint and alternative.')[:120]}",
        },
        {
            "id": "proj_outcome",
            "topic": "Outcome & Learning",
            "prompt": f"How did you verify {title} worked, and what is the biggest engineering lesson you took from it?",
            "tip": "Distinguish what you verified from what is not yet measured.",
        },
    ]


def extract_resume_topics_and_questions(raw_text: str) -> dict[str, Any]:
    clean = raw_text.strip()
    lines = [line.strip(" -•*\t") for line in clean.splitlines() if line.strip()]
    lower = clean.lower()

    skills_found: list[str] = []
    for tech in KNOWN_TECH_TERMS:
        if re.search(r"(?<![a-z0-9])" + re.escape(tech) + r"(?![a-z0-9])", lower):
            skills_found.append(tech.upper() if len(tech) <= 3 and tech != "go" else tech.title() if tech.islower() else tech)

    action_re = re.compile(
        r"\b(built|developed|designed|implemented|created|led|engineered|migrated|tested|automated|reduced|improved|integrated|deployed)\b",
        re.I,
    )
    highlights = [line for line in lines if len(line) >= 20 and action_re.search(line)][:6]
    if not highlights:
        highlights = [line for line in lines if len(line) >= 18][:4]

    metric_lines = [
        line for line in lines
        if re.search(r"\b\d+(?:%|ms|s|x|k|mb|gb|\+|\s*(?:users|students|tests|endpoints|queries))\b", line, re.I)
    ][:3]

    questions: list[dict[str, Any]] = []
    if highlights:
        first_claim = highlights[0][:140]
        questions.append({
            "id": "resume_claim_1",
            "topic": "Experience deep dive",
            "prompt": f'Your resume mentions: "{first_claim}". Walk me through how you built and verified this.',
            "tip": "Break it down into goal, your exact implementation, and how you tested it.",
        })
    if len(highlights) >= 2:
        second_claim = highlights[1][:140]
        questions.append({
            "id": "resume_claim_2",
            "topic": "Technical challenge",
            "prompt": f'Looking at "{second_claim}", what was the hardest technical obstacle you ran into and how did you solve it?',
            "tip": "Explain what failed first and what evidence guided your fix.",
        })
    if skills_found:
        top_skills = ", ".join(skills_found[:4])
        questions.append({
            "id": "resume_skills",
            "topic": "Technology choices",
            "prompt": f"You list {top_skills}. Pick one and explain why it fit your project better than an alternative.",
            "tip": "Discuss one concrete strength and one limitation of the tool.",
        })
    if metric_lines:
        metric_excerpt = metric_lines[0][:140]
        questions.append({
            "id": "resume_metric",
            "topic": "Verifying outcomes",
            "prompt": f'You noted "{metric_excerpt}". How did you measure or observe that result?',
            "tip": "Be honest about how you tested it and any constraints on the measurement.",
        })
    questions.append({
        "id": "resume_reflection",
        "topic": "Reflection",
        "prompt": "Across the projects on your resume, which decision would you reconsider if you rebuilt it today?",
        "tip": "Show mature engineering judgement rather than perfection.",
    })

    return {
        "detected_skills": skills_found[:16],
        "extracted_highlights": highlights,
        "metric_claims": metric_lines,
        "questions": questions[:6],
        "note": "Extracted locally using deterministic keyword and sentence matching. Review and edit questions to match your exact work.",
    }


def _build_mock_debrief(record: dict[str, Any]) -> dict[str, Any]:
    questions = json.loads(record["questions_json"])
    responses = json.loads(record["responses_json"])
    by_qid = {r["question_id"]: r for r in responses}

    question_reviews: list[dict[str, Any]] = []
    analytics_list: list[dict[str, Any]] = []
    strengths: list[str] = []
    areas_to_improve: list[str] = []

    answered_count = 0
    for q in questions:
        resp = by_qid.get(q["id"])
        answer_text = (resp.get("answer_text") or "").strip() if resp else ""
        if answer_text:
            answered_count += 1
        dur = resp.get("speaking_duration_seconds") if resp else None
        pauses = resp.get("pause_count") if resp else None
        silence = resp.get("silence_seconds") if resp else None
        analytics = analyze_transcript(
            answer_text,
            duration_seconds=dur,
            pause_count=pauses,
            silence_seconds=silence,
        )
        analytics_list.append(analytics)
        question_reviews.append({
            "question_id": q["id"],
            "topic": q.get("topic", "Interview prompt"),
            "prompt": q["prompt"],
            "answer_text": answer_text,
            "answered": bool(answer_text),
            "speaking_analytics": analytics,
        })

    delivery = summarize_session_delivery(analytics_list)

    if answered_count == len(questions) and answered_count > 0:
        strengths.append(f"Completed all {answered_count} prompts in this session.")
    elif answered_count > 0:
        areas_to_improve.append(f"Answered {answered_count} of {len(questions)} prompts; try giving even a 2-sentence answer to skipped prompts next time.")
    else:
        areas_to_improve.append("No written or spoken responses were submitted in this session.")

    if delivery["relevant_vocabulary"]:
        strengths.append("Used concrete technical/professional terms: " + ", ".join(delivery["relevant_vocabulary"][:6]) + ".")
    if delivery["average_wpm"] is not None:
        if 105 <= delivery["average_wpm"] <= 160:
            strengths.append(f"Spoke at a clear conversational pace ({delivery['average_wpm']} WPM).")
        elif delivery["average_wpm"] > 175:
            areas_to_improve.append(f"Speaking pace averaged {delivery['average_wpm']} WPM; pause for a beat after key points.")
        else:
            strengths.append(f"Kept an unhurried delivery ({delivery['average_wpm']} WPM).")

    if delivery["total_fillers"] > 0:
        areas_to_improve.append(f"Detected {delivery['total_fillers']} filler word(s) across transcripts; practise silent half-second pauses instead.")
    if delivery["long_sentence_count"] > 0:
        areas_to_improve.append(f"{delivery['long_sentence_count']} very long sentence(s) detected; break complex points into shorter spoken statements.")
    if delivery["grammar_hint_count"] > 0:
        areas_to_improve.append(f"{delivery['grammar_hint_count']} phrasing pattern(s) flagged for review in your transcript highlights.")
    if not strengths and answered_count > 0:
        strengths.append("Put real thoughts into words locally—revisit one prompt and add a concrete example or result.")

    followups = [
        {"title": "Review highlighted transcript moments", "action": "Inspect fillers, repeated words, and phrasing notes below."},
        {"title": "Save 1-2 sharper sentences to Memory", "action": "Turn strong phrasings into quick spaced-review cards."},
        {"title": "Retry one tricky prompt aloud", "action": "Focus on one improvement rather than everything at once."},
    ]

    if len(question_reviews) == 3 and question_reviews[0]["question_id"] == "fluency_432_r1":
        r1 = question_reviews[0]["speaking_analytics"]
        r3 = question_reviews[2]["speaking_analytics"]
        if r1["word_count"] > 0 and r3["word_count"] > 0:
            filler_diff = r3["filler_total"] - r1["filler_total"]
            if filler_diff < 0:
                strengths.append(f"4/3/2 Fluency Drill: filler words dropped by {abs(filler_diff)} from Round 1 to Round 3.")
            if r1["wpm"] is not None and r3["wpm"] is not None:
                strengths.append(f"4/3/2 Pace progression: Round 1 ({r1['wpm']} WPM) -> Round 3 ({r3['wpm']} WPM) on the same topic.")

    return {
        "mock_id": record["id"],
        "mode": record["mode"],
        "title": record["title"],
        "status": record["status"],
        "questions_attempted": len(responses),
        "responses_completed": answered_count,
        "total_questions": len(questions),
        "time_limit_seconds": record["time_limit_seconds"],
        "elapsed_seconds": record["elapsed_seconds"],
        "delivery_summary": delivery,
        "question_reviews": question_reviews,
        "strengths": strengths,
        "areas_to_improve": areas_to_improve,
        "recommended_followups": followups,
        "disclaimer": "This debrief summarizes your actual answers, timing, and deterministic transcript checks. It does not score ability or predict placement outcomes.",
    }


class ProjectPayload(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    problem: str = Field(default="", max_length=2000)
    approach: str = Field(default="", max_length=2000)
    implementation: str = Field(default="", max_length=2000)
    decisions_tradeoffs: str = Field(default="", max_length=2000)
    outcome: str = Field(default="", max_length=2000)
    learning: str = Field(default="", max_length=2000)
    tech_stack: str = Field(default="", max_length=400)
    personal_role: str = Field(default="", max_length=240)
    notes: str = Field(default="", max_length=3000)
    source_kind: Literal["project", "resume"] = "project"

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Give your project a short title.")
        return cleaned


class ResumeParsePayload(BaseModel):
    resume_text: str = Field(min_length=20, max_length=50_000)
    title: str = Field(default="Resume Preparation", max_length=140)
    save_as_project: bool = False


class MockStartPayload(BaseModel):
    mode: Literal["timed_mock", "warmup", "project_studio", "resume_prep", "fluency_432"] = "timed_mock"
    focus: Literal["mixed", "project", "hr", "technical", "workplace"] = "mixed"
    question_count: int = Field(default=5, ge=2, le=6)
    time_limit_seconds: int | None = Field(default=600, ge=60, le=3600)
    project_id: str | None = Field(default=None, max_length=120)
    custom_questions: list[dict[str, Any]] | None = None
    title: str | None = Field(default=None, max_length=160)
    fluency_prompt: str | None = Field(default=None, max_length=400)


class MockResponsePayload(BaseModel):
    question_id: str = Field(min_length=1, max_length=120)
    answer_text: str = Field(default="", max_length=6000)
    elapsed_seconds: int = Field(default=0, ge=0, le=7200)
    speaking_duration_seconds: float | None = Field(default=None, ge=0, le=3600)
    pause_count: int | None = Field(default=None, ge=0, le=500)
    silence_seconds: float | None = Field(default=None, ge=0, le=3600)


class MockFinishPayload(BaseModel):
    elapsed_seconds: int = Field(default=0, ge=0, le=7200)


def _project_from_row(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["generated_questions"] = json.loads(item.pop("generated_questions_json") or "[]")
    return item


def _mock_view(row: Any) -> dict[str, Any]:
    item = dict(row)
    questions = json.loads(item.pop("questions_json") or "[]")
    responses = json.loads(item.pop("responses_json") or "[]")
    answered_ids = {r["question_id"] for r in responses}
    current = next((q for q in questions if q["id"] not in answered_ids), None)
    return {
        **item,
        "questions": questions,
        "responses": responses,
        "question_count": len(questions),
        "answered_count": len(responses),
        "current_question": current,
    }


def create_career_prep_router(db_path: Path) -> APIRouter:
    router = APIRouter(prefix="/api/career", tags=["career-prep"])

    @router.get("/projects")
    def list_projects() -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            rows = conn.execute("SELECT * FROM learner_projects ORDER BY updated_at DESC LIMIT 50").fetchall()
        return {"projects": [_project_from_row(r) for r in rows]}

    @router.post("/projects", status_code=201)
    def create_project(payload: ProjectPayload) -> dict[str, Any]:
        pid = str(uuid4())
        now = _now()
        data = payload.model_dump()
        questions = build_project_questions(data)
        with connect_database(Path(db_path)) as conn:
            conn.execute(
                """
                INSERT INTO learner_projects
                    (id, title, problem, approach, implementation, decisions_tradeoffs, outcome,
                     learning, tech_stack, personal_role, notes, source_kind, generated_questions_json,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid, data["title"], data["problem"].strip(), data["approach"].strip(),
                    data["implementation"].strip(), data["decisions_tradeoffs"].strip(),
                    data["outcome"].strip(), data["learning"].strip(), data["tech_stack"].strip(),
                    data["personal_role"].strip(), data["notes"].strip(), data["source_kind"],
                    json.dumps(questions, ensure_ascii=False), now, now,
                ),
            )
            row = conn.execute("SELECT * FROM learner_projects WHERE id = ?", (pid,)).fetchone()
        return {"project": _project_from_row(row)}

    @router.put("/projects/{project_id}")
    def update_project(project_id: str, payload: ProjectPayload) -> dict[str, Any]:
        now = _now()
        data = payload.model_dump()
        questions = build_project_questions(data)
        with connect_database(Path(db_path)) as conn:
            existing = conn.execute("SELECT id FROM learner_projects WHERE id = ?", (project_id,)).fetchone()
            if existing is None:
                raise HTTPException(status_code=404, detail="Saved project not found.")
            conn.execute(
                """
                UPDATE learner_projects
                SET title=?, problem=?, approach=?, implementation=?, decisions_tradeoffs=?,
                    outcome=?, learning=?, tech_stack=?, personal_role=?, notes=?,
                    generated_questions_json=?, updated_at=?
                WHERE id=?
                """,
                (
                    data["title"], data["problem"].strip(), data["approach"].strip(),
                    data["implementation"].strip(), data["decisions_tradeoffs"].strip(),
                    data["outcome"].strip(), data["learning"].strip(), data["tech_stack"].strip(),
                    data["personal_role"].strip(), data["notes"].strip(),
                    json.dumps(questions, ensure_ascii=False), now, project_id,
                ),
            )
            row = conn.execute("SELECT * FROM learner_projects WHERE id = ?", (project_id,)).fetchone()
        return {"project": _project_from_row(row)}

    @router.delete("/projects/{project_id}", status_code=204)
    def delete_project(project_id: str) -> None:
        with connect_database(Path(db_path)) as conn:
            cur = conn.execute("DELETE FROM learner_projects WHERE id = ?", (project_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Saved project not found.")
        return None

    @router.post("/resume/parse")
    def parse_resume(payload: ResumeParsePayload) -> dict[str, Any]:
        extracted = extract_resume_topics_and_questions(payload.resume_text)
        saved_project = None
        if payload.save_as_project:
            pid = str(uuid4())
            now = _now()
            title = payload.title.strip() or "Resume Preparation"
            with connect_database(Path(db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO learner_projects
                        (id, title, problem, approach, implementation, decisions_tradeoffs, outcome,
                         learning, tech_stack, personal_role, notes, source_kind, generated_questions_json,
                         created_at, updated_at)
                    VALUES (?, ?, '', '', '', '', '', '', ?, '', ?, 'resume', ?, ?, ?)
                    """,
                    (
                        pid, title, ", ".join(extracted["detected_skills"]),
                        payload.resume_text[:3000],
                        json.dumps(extracted["questions"], ensure_ascii=False), now, now,
                    ),
                )
                row = conn.execute("SELECT * FROM learner_projects WHERE id = ?", (pid,)).fetchone()
                saved_project = _project_from_row(row)
        return {**extracted, "saved_project": saved_project}

    @router.get("/mocks")
    def list_mocks() -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            rows = conn.execute("SELECT * FROM mock_interviews ORDER BY created_at DESC LIMIT 50").fetchall()
        return {"mocks": [_mock_view(r) for r in rows]}

    @router.post("/mocks", status_code=201)
    def start_mock(payload: MockStartPayload) -> dict[str, Any]:
        mid = str(uuid4())
        now = _now()
        questions: list[dict[str, Any]] = []
        title = (payload.title or "").strip()
        time_limit = payload.time_limit_seconds

        persisted_mode = "warmup" if payload.mode == "fluency_432" else payload.mode
        if payload.mode == "fluency_432":
            questions = build_fluency_432_rounds(payload.fluency_prompt)
            title = title or "4/3/2 Oral Fluency Drill (90s -> 60s -> 45s)"
            time_limit = payload.time_limit_seconds or 240
        elif payload.mode == "warmup":
            questions = list(WARMUP_QUESTIONS)
            title = title or "5-Minute Interview Warm-up"
            time_limit = payload.time_limit_seconds or 300
        elif payload.mode == "project_studio" and payload.project_id:
            with connect_database(Path(db_path)) as conn:
                prow = conn.execute("SELECT * FROM learner_projects WHERE id = ?", (payload.project_id,)).fetchone()
            if prow is None:
                raise HTTPException(status_code=404, detail="Selected project was not found.")
            proj = _project_from_row(prow)
            questions = proj["generated_questions"] or build_project_questions(proj)
            title = title or f"Project Practice · {proj['title']}"
        elif payload.custom_questions:
            for idx, q in enumerate(payload.custom_questions[:6], start=1):
                prompt_text = str(q.get("prompt", "")).strip()
                if prompt_text:
                    questions.append({
                        "id": str(q.get("id") or f"custom_{idx}")[:60],
                        "topic": str(q.get("topic") or "Preparation topic")[:80],
                        "prompt": prompt_text[:500],
                        "tip": str(q.get("tip") or "Give a clear, structured answer with one specific example.")[:240],
                    })
            title = title or "Resume Preparation Session"
        else:
            if payload.focus == "mixed":
                pool = [
                    MOCK_QUESTION_BANK["hr"][0],
                    MOCK_QUESTION_BANK["project"][0],
                    MOCK_QUESTION_BANK["project"][1],
                    MOCK_QUESTION_BANK["technical"][0],
                    MOCK_QUESTION_BANK["hr"][1],
                    MOCK_QUESTION_BANK["technical"][2],
                ]
            else:
                pool = MOCK_QUESTION_BANK.get(payload.focus, MOCK_QUESTION_BANK["project"])
            questions = pool[: payload.question_count]
            focus_labels = {"mixed": "Mixed Placement", "project": "Project Deep Dive", "hr": "HR & Behavioural", "technical": "Technical Fundamentals", "workplace": "Workplace Engineering"}
            title = title or f"Timed Mock · {focus_labels[payload.focus]}"

        if not questions:
            raise HTTPException(status_code=400, detail="At least one question is required to start a session.")

        with connect_database(Path(db_path)) as conn:
            conn.execute(
                """
                INSERT INTO mock_interviews
                    (id, mode, title, time_limit_seconds, elapsed_seconds, status,
                     questions_json, responses_json, project_id, created_at, completed_at)
                VALUES (?, ?, ?, ?, 0, 'in_progress', ?, '[]', ?, ?, NULL)
                """,
                (mid, persisted_mode, title[:160], time_limit, json.dumps(questions, ensure_ascii=False), payload.project_id, now),
            )
            row = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mid,)).fetchone()
        return {"mock": _mock_view(row)}

    @router.post("/mocks/{mock_id}/respond")
    def submit_mock_response(mock_id: str, payload: MockResponsePayload) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mock_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Mock interview session not found.")
            if row["status"] != "in_progress":
                raise HTTPException(status_code=409, detail="This mock interview is already finished.")
            questions = json.loads(row["questions_json"])
            responses = json.loads(row["responses_json"])
            valid_ids = {q["id"] for q in questions}
            if payload.question_id not in valid_ids:
                raise HTTPException(status_code=400, detail="Question does not belong to this mock interview.")
            responses = [r for r in responses if r["question_id"] != payload.question_id]
            responses.append({
                "question_id": payload.question_id,
                "answer_text": payload.answer_text.strip(),
                "speaking_duration_seconds": payload.speaking_duration_seconds,
                "pause_count": payload.pause_count,
                "silence_seconds": payload.silence_seconds,
                "submitted_at": _now(),
            })
            elapsed = max(int(row["elapsed_seconds"]), int(payload.elapsed_seconds))
            is_done = len(responses) >= len(questions)
            status_val = "completed" if is_done else "in_progress"
            completed_at = _now() if is_done else None
            conn.execute(
                "UPDATE mock_interviews SET responses_json=?, elapsed_seconds=?, status=?, completed_at=? WHERE id=?",
                (json.dumps(responses, ensure_ascii=False), elapsed, status_val, completed_at, mock_id),
            )
            updated = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mock_id,)).fetchone()
        result: dict[str, Any] = {"mock": _mock_view(updated)}
        if updated["status"] == "completed":
            result["debrief"] = _build_mock_debrief(dict(updated))
        return result

    @router.post("/mocks/{mock_id}/finish")
    def finish_mock(mock_id: str, payload: MockFinishPayload) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mock_id,)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Mock interview session not found.")
            elapsed = max(int(row["elapsed_seconds"]), int(payload.elapsed_seconds))
            conn.execute(
                "UPDATE mock_interviews SET status='completed', elapsed_seconds=?, completed_at=COALESCE(completed_at, ?) WHERE id=?",
                (elapsed, _now(), mock_id),
            )
            updated = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mock_id,)).fetchone()
        return {"mock": _mock_view(updated), "debrief": _build_mock_debrief(dict(updated))}

    @router.get("/mocks/{mock_id}/debrief")
    def get_mock_debrief(mock_id: str) -> dict[str, Any]:
        with connect_database(Path(db_path)) as conn:
            row = conn.execute("SELECT * FROM mock_interviews WHERE id = ?", (mock_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Mock interview session not found.")
        return {"debrief": _build_mock_debrief(dict(row))}

    @router.delete("/mocks/{mock_id}", status_code=204)
    def delete_mock(mock_id: str) -> None:
        with connect_database(Path(db_path)) as conn:
            cur = conn.execute("DELETE FROM mock_interviews WHERE id = ?", (mock_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Mock interview session not found.")
        return None

    return router
