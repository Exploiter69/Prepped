# Prepped — Current State

**Updated:** 2026-10-24  
**Source of truth:** GitHub `main`  
**Product stage:** Local text MVP; preparing for fresh-checkout acceptance and first student usability pilot.

## Implemented

- One versioned project-explanation scenario with five prompts and a versioned rubric.
- FastAPI backend with a plain HTML/CSS/JavaScript interface.
- SQLite local session storage and additive migrations.
- Ordered answer capture, empty-answer handling, cancellation, completion, and answer-length limits.
- Deterministic feedback with evidence excerpts, prompt-specific next actions, explicit uncertainty, and no overall score.
- Checklist feedback uses distinct sentence-level evidence where available; follow-up handling checks prompt-specific phrase signals. These are heuristics, not semantic validation.
- Retry with scenario/rubric snapshot, attempt grouping/comparison data, local history, and session deletion.
- Regression tests for core flow, feedback grounding/limitations, empty answers, cancellation, boundaries, retry, history, and deletion.
- No mandatory AI account, paid API, hosted database, or raw audio capture.

## Recent changes

- PR [#7 — Fix feedback signals for pasted answers](https://github.com/Exploiter69/Prepped/pull/7) merged on 2026-10-24 as `4bf7774810bd76ae904505109f4dab49dbec23ba`. Its GitHub Actions test workflow passed. It normalizes curly apostrophes and typographic dashes, recognizes common reflection wording, and avoids counting explicitly denied testing as positive test evidence.
- PR [#6 — Improve evidence quality in the practice checklist](https://github.com/Exploiter69/Prepped/pull/6) merged on 2026-10-24 as `c547dea5a43b917ddcffda89fbcfeaf01577c504`. Its GitHub Actions test workflow passed.

## Not yet evidenced / remaining

- A fresh-checkout install, test, and browser smoke test after the merge.
- Manual confirmation of persistence across app restart and understandable attempt comparison.
- Student usability pilot and its report.
- Feedback quality review by students or faculty.
- Local speech-to-text/text-to-speech benchmark on the target laptop.
- Human-rater calibration or any measured placement/learning improvement.

## Immediate acceptance commands

From the repository root, after syncing `main`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn prepped.main:app --reload
```

Open `http://127.0.0.1:8000`, complete the five-question scenario, review the feedback, retry it, compare attempts, restart the server to check history persistence, then delete a session and verify it disappears. The database is local at `data/prepped.sqlite3` by default; do not put real personal or confidential interview data into the prototype.

## Product boundaries

Prepped is a practice prototype, not an official assessment, hiring decision, or placement predictor. Feedback signals are simple heuristics and can be wrong. Voice and advanced features remain gated on usability evidence and zero-cost feasibility.
