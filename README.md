# Prepped

**Prepped helps Indian engineering students practise placement and professional conversations, get specific feedback tied to their answers, and improve through repeated practice.**

Prepped is an evidence-led, local-first practice app. The first working slice is a **text-based project-interview scenario**. It deliberately avoids paid services, mandatory AI, overall scores, and claims about placement outcomes.

## Start here

- [Current implementation and acceptance status](docs/CURRENT_STATE.md)
- [Student usability pilot protocol](docs/PILOT_PROTOCOL.md)
- [Complete Product and System Blueprint](docs/PRODUCT_BLUEPRINT.md)
- [Architecture Decision Record 001](docs/ADR-001-MINIMAL-LOCAL-FIRST-ARCHITECTURE.md)
- [Complete Project Roadmap](docs/COMPLETE_ROADMAP.md)
- [Research Review and Decision Matrix](docs/RESEARCH_DECISION_MATRIX.md)
- [Research archive verification](research/raw/VERIFICATION.md)
- [Upstream repository audit](docs/UPSTREAM_REPOSITORY_AUDIT.md)
- [Upstream feature mapping](docs/UPSTREAM_FEATURE_MAPPING.md)

## First scenario

**Explain your project to a placement interviewer.** The learner answers five prompts about the problem, personal contribution, a design decision, evidence, and reflection. After the final answer, Prepped shows question-by-question notes and a transparent checklist, then supports retry, attempt comparison, local history, and deletion.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn prepped.main:app --reload
```

Open `http://127.0.0.1:8000`. The health endpoint is `/api/health`; the scenario definition is `/api/scenarios/project-explanation`. SQLite is created at `data/prepped.sqlite3` on startup. The data directory and database files are ignored by Git.

Run tests:

```bash
python -m pytest
```

## What the first loop does

- Creates a local session and saves a snapshot of its scenario and rubric version.
- Saves one answer per prompt in order, supports skipping with an empty answer, and caps each answer at 6,000 characters.
- Completes the session after the final prompt; prevents out-of-order or post-completion answers.
- Produces deterministic, explainable feedback with excerpts from submitted text and a concrete next action.
- Shows when there is not enough evidence instead of inventing an answer or forcing a score.
- Supports retry against the same scenario/rubric snapshot and compares checklist labels across attempts.
- Lists up to 100 local sessions, allows an in-progress session to resume, and deletes a session with its answers.
- Uses SQLite foreign-key enforcement on every connection and applies additive schema migrations to the starter database.

## Feedback limitations

Feedback is a simple text heuristic, **not a validated assessment, AI interviewer, or placement predictor**. It checks a few explicit text and length signals. Those signals can miss good answers or flag weak ones; they do not measure spoken delivery, pronunciation, listener understanding, or actual learning outcomes. There is no overall score. Do not invent project details, results, metrics, or evidence to satisfy the checklist.

## Project constraints

- ₹0 mandatory spending: no required paid APIs, subscriptions, hosting, or usage-based services.
- Local-first development with Python, FastAPI, plain HTML/CSS/JavaScript, SQLite, and versioned JSON.
- No model or API credentials required; no answer text is sent to an AI service.
- No raw audio is collected in this text-only slice.
- GitHub is the source of truth.

## Current status

The local text practice loop is implemented on `main`, including deterministic feedback, retry, attempt comparison, local history, and session deletion. PR #6 improved checklist evidence selection; PR #7 fixed Unicode apostrophe matching and prevented explicitly denied testing from counting as positive test evidence. PR #7’s GitHub Actions test run passed before merge. Automated tests cover the core API flow, but a clean-checkout setup check and a human student pilot are still outstanding. Voice remains gated on pilot findings and measured feasibility on the target hardware.
