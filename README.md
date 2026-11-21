# Prepped

**Prepped is a local-first, voice-enabled practice environment for Indian engineering students working on placement preparation, professional communication, English fluency, and technical interview practice.**

The product direction is **voice-first and personalised over time**. The existing text practice loop remains the reliable fallback. Voice supports record/stop capture, an editable transcript, and spoken interviewer prompts. Speech recognition can run locally with Vosk or, when explicitly configured, through Groq Whisper for stronger multilingual transcription.

This repository does **not** claim validated speech accuracy, placement improvement, or an AI interviewer. No paid service is required. Optional Groq transcription sends recordings to Groq; without a Groq key, the app uses local Vosk.

## Start here

- [Current implementation and verification status](docs/CURRENT_STATE.md)
- [Clean install, supported environment and recovery](docs/INSTALL.md)
- [Security boundaries and release hardening](docs/RELEASE_HARDENING.md)
- [A–F learner acceptance checklist](docs/ACCEPTANCE_CHECKLIST.md)
- [Phase G release hardening and acceptance record](docs/PHASE_G_ACCEPTANCE.md)
- [Phase H adaptive learning implementation and acceptance gates](docs/PHASE_H_ACCEPTANCE.md)
- [Phase I voice intelligence implementation and acceptance gates](docs/PHASE_I_ACCEPTANCE.md)
- [Voice setup, privacy, and troubleshooting](docs/VOICE.md)
- [Phase J curriculum quality and learner-validation gates](docs/PHASE_J_ACCEPTANCE.md)
- [Phase K security, privacy, and reliability acceptance](docs/PHASE_K_ACCEPTANCE.md)
- [Phase L local release-candidate acceptance](docs/PHASE_L_ACCEPTANCE.md)
- [UI Stage 9 final UI acceptance and release integration](docs/UI_STAGE_9_ACCEPTANCE.md)
- [Offline text-mode demonstration](docs/DEMO.md)
- [Changelog](CHANGELOG.md)
- [ADR-002: local voice slice](docs/ADR-002-LOCAL-VOICE-SLICE.md)
- [ADR-003: optional Groq Whisper transcription](docs/ADR-003-GROQ-WHISPER-TRANSCRIPTION.md)
- [Complete Product and System Blueprint](docs/PRODUCT_BLUEPRINT.md)
- [Complete Project Roadmap](docs/COMPLETE_ROADMAP.md)
- [Product implementation sequence and release gates](docs/PRODUCT_ROADMAP.md) · [Current build status and next actions](docs/CURRENT_STATE.md)
- [Student usability pilot protocol](docs/PILOT_PROTOCOL.md) — future validation, not an engineering blocker
- [Architecture Decision Record 001: text architecture](docs/ADR-001-MINIMAL-LOCAL-FIRST-ARCHITECTURE.md)
- [Research Review and Decision Matrix](docs/RESEARCH_DECISION_MATRIX.md)
- [Research archive verification](research/raw/VERIFICATION.md)

## First scenario

**Explain your project to a placement interviewer.** The learner answers five prompts about the problem, personal contribution, a design decision, evidence, and reflection. Answers can be typed or spoken. Spoken answers are transcribed into an editable text box (locally with Vosk, or remotely with Groq when explicitly configured), then submitted through the same session API as typed answers. The UI discloses which transcription mode is active before recording. After the final answer, Prepped shows question-by-question notes and a transparent checklist, then supports retry, attempt comparison, local history, and deletion. Career studios add authored contextual follow-ups, optional simpler prompt wording and hints, answer-specific formative coaching, and a previous/current answer comparison after retry. Learners can explicitly save an answer or coaching action to Memory or add a future studio practice to the daily plan. These cues are not an interview score or correctness assessment.



## Learning workspace — Phase B engine and Phase C English curriculum

The Learning entry in the header opens a reusable lesson workspace built on the same FastAPI + SQLite + plain JavaScript stack. The current versioned curriculum includes 14 stable skills, one foundation stage, nine units, four tracks, 13 authored lessons plus a separate low-stakes baseline check. The English foundations track contains 11 sequenced lessons across sentence construction, grammar, vocabulary, listening, speaking, and pronunciation.

The lesson runner displays each lesson's learning outcomes before exercises and supports:
- Single-choice and contextual vocabulary exercises.
- Sentence/idea ordering.
- Listening comprehension using the configured local TTS endpoint, with replay controls and a revealable text alternative.
- Structured speaking practice for descriptions, process/feature explanations, retelling, opinions, and follow-up responses; text input remains available when speech input is unavailable.
- Listen-and-repeat pronunciation activities using local TTS model phrases, optional recording/transcription, and private self-review. No pronunciation, accent, phoneme, or fluency score is generated.
- Short written or spoken responses. Spoken responses use the existing STT endpoint; Groq use is disclosed before recording, and raw audio is not stored by Prepped.
- Deterministic answer feedback for closed exercises; open responses are saved for learner self-review and are not automatically graded.
- Ordered attempts, prerequisite enforcement, restart-safe resume, and progress events.

The saved learner goal and focus areas select an explainable starter route through the English and project-communication tracks. The optional Starting point check records sentence, listening, and project-response tasks for later comparison. It can be repeated and reviewed; it assigns no proficiency level or total score. The progress view reports recorded activity counts, not proficiency or learning gains. Open speaking and pronunciation responses are saved for self-review, not automatically graded. Advanced diagnostic interpretation remains future work. Learner-controlled revision is implemented in Phase D, and the Career workspace's project, HR/behavioural, and technical interview studios are implemented in Phase E. Phase F adds the cross-module progress and recovery view.

Learning API: GET /api/learning/catalog, GET /api/learning/recommendations, POST /api/learning/attempts, GET /api/learning/attempts/{id}, POST /api/learning/attempts/{id}/responses, GET /api/learning/progress, and GET /api/learning/diagnostic/latest.

## Run locally

Requires Python 3.11 or newer. The voice slice also uses `ffmpeg` to decode browser recordings and a local speech model. Text mode works without either.

```bash
bash scripts/prepped.sh setup
bash scripts/prepped.sh start
```

The helper installs the application plus local test/browser tooling, starts the server in the foreground on 127.0.0.1, and stops when you press Ctrl+C. For a minimal runtime-only install, create a virtual environment and run `python -m pip install -e .`; then start Uvicorn with the loopback command below. The supported install is a source checkout; wheel/binary packaging is not claimed.

Open `http://127.0.0.1:8000`. Keep the server bound to loopback; do not expose the prototype on a LAN or public network. Health/readiness endpoints are `/api/health` and `/api/ready`; voice provider availability is `/api/voice/status`. See [INSTALL.md](docs/INSTALL.md) for clean install and recovery instructions, or run `bash scripts/prepped.sh check` while the app is running.

### Enable local voice

Models are **not downloaded at application startup**. Install them explicitly once:

```bash
# Vosk STT + optional Piper TTS + Piper voice (~160 MB of downloads)
./scripts/setup_voice.sh

# Or speech-to-text only; espeak-ng is used for prompts if installed
./scripts/setup_voice.sh --stt-only
```

On Arch/Omarchy, the system tools are:

```bash
sudo pacman -S ffmpeg espeak-ng
```

See [docs/VOICE.md](docs/VOICE.md) for model paths, environment overrides, licensing, privacy, and troubleshooting.

### Optional higher-accuracy transcription (Groq)

Create a free Groq API key, then set it only in the server environment:

```bash
export GROQ_API_KEY="your-key"
python -m uvicorn prepped.main:app --reload
```

Install the optional HTTP client with `python -m pip install -e ".[voice-cloud]"`. When the key is present, Prepped uses `whisper-large-v3`; without it, Prepped uses local Vosk. The key is never sent to the browser. Groq mode sends the recording to Groq, so use practice audio only and review the provider's data controls. Do not enable a paid plan for this demo.

Run tests:

```bash
python3 -m pytest
```

The real Vosk integration test is skipped on a clean checkout unless the model has been installed. It runs locally after `./scripts/setup_voice.sh`.

## What the voice slice does

- Keeps the existing typed answer workflow fully functional.
- Requests microphone access only when the learner presses **Start recording**.
- Records a bounded turn with **Start recording** / **Stop recording**; no always-listening agent.
- Sends the browser recording to the local FastAPI app and decodes it in memory with `ffmpeg`.
- Uses Groq Whisper (`whisper-large-v3`) when `GROQ_API_KEY` is configured; otherwise uses local Vosk.
- Inserts the transcript into the existing answer box so the learner can correct recognition errors before saving.
- Submits the corrected text through the existing `POST /api/sessions/{id}/answers` endpoint.
- Synthesises interviewer prompts with local Piper TTS when available, falling back to local `espeak-ng`.
- Provides **Play question aloud**, **Stop**, and **Replay** controls.
- Shows clear microphone/model/TTS errors and keeps text mode usable when voice fails.
- Does not save raw audio locally. With Groq configured, the audio is sent to Groq for transcription; without it, transcription stays local.

## What the text loop does

- Creates a local session and saves a snapshot of its scenario and rubric version.
- Saves one answer per prompt in order, supports skipping with an empty answer, and caps each answer at 6,000 characters.
- Completes the session after the final prompt; prevents out-of-order or post-completion answers.
- Produces deterministic, explainable feedback with excerpts from submitted text and a concrete next action.
- Shows when there is not enough evidence instead of inventing an answer or forcing a score.
- Supports retry against the same scenario/rubric snapshot and compares checklist labels across attempts.
- Lists up to 100 local sessions, allows an in-progress session to resume, and deletes a session with its answers.
- Uses SQLite foreign-key enforcement on every connection and applies additive schema migrations to the starter database.

## Feedback limitations

Feedback is a simple text heuristic, **not a validated assessment, AI interviewer, or placement predictor**. It checks a few explicit text and length signals. Those signals can miss good answers or flag weak ones; they do not measure spoken delivery, pronunciation, listener understanding, speech-recognition accuracy, or actual learning outcomes. There is no overall score. Do not invent project details, results, metrics, or evidence to satisfy the checklist.

The text feedback system is frozen for this phase. Do not keep adding phrase heuristics; future feedback work should be a separately designed, evidence-led change.

## Voice limitations

- Speech recognition accuracy is **not validated**, especially for Indian English accents and real student speech.
- Local Vosk is a CPU-friendly fallback and can produce incorrect words. Groq Whisper is the optional higher-accuracy cloud path; its accuracy on this project's users still needs testing. The transcript remains editable.
- TTS quality and the first-token/load latency have not been benchmarked across devices.
- The first milestone is record/stop only. There is no streaming, interruption handling, VAD, or realtime agent.
- A browser microphone session must still be checked manually on the target machine; automated tests cover the API, adapters, failure paths, and a synthetic real-model integration check.
- No LLM feedback, pronunciation scoring, or emotion/personality inference is added to the voice pipeline.

## Privacy

- Answers are stored in a local SQLite database; microphone audio is decoded and transcribed in memory and is not saved.
- No raw audio is stored by Prepped. Local Vosk mode sends no audio remotely.
- Optional Groq mode sends audio to Groq; review its data controls and privacy terms before use. Corrected answer text is stored locally only.
- Local history can be deleted from the interface.
- Model files are local and ignored by Git. Do not commit model weights or personal recordings.

## Project constraints

- ₹0 mandatory spending: no required paid APIs, subscriptions, hosting, or usage-based services.
- Local-first development with Python, FastAPI, plain HTML/CSS/JavaScript, SQLite, and versioned JSON.
- No React/Vue/Svelte migration, no hosted database, no queues, no microservices, no vector store.
- No required model or API credentials. Remote transcription is opt-in via a server-side environment variable; answer text is not sent to an AI service.
- GitHub is the source of truth.
- The student pilot is future user validation, not a prerequisite for engineering development. No pilot results are claimed.

## Current status (2026-11-20)

Phases A–H are implemented; Phases I and J have implementation in place with target-device/human acceptance still open. Phase K engineering verification is complete: the target laptop passed 172 tests and exact-commit CI [44754505687](https://github.com/Exploiter69/Prepped/actions/runs/44754505687) succeeded. Phase L is building the local release-candidate workflow; it is not yet a release. Real microphone/STT/TTS, screen-reader/accessibility, restore interruption, clean-install and learner-validation checks remain open. See [Current State](docs/CURRENT_STATE.md), [Phase I](docs/PHASE_I_ACCEPTANCE.md), [Phase J](docs/PHASE_J_ACCEPTANCE.md), [Phase K](docs/PHASE_K_ACCEPTANCE.md), and [Phase L](docs/PHASE_L_ACCEPTANCE.md).


## Personal learning memory and revision (Phase D)

The Learning workspace includes an optional, learner-controlled memory library. Save words, phrases, corrections, concepts, and examples manually, or use a lesson-feedback suggestion to prefill an editable form. Nothing is stored from a suggestion until the learner submits it. Lesson-derived notes retain their source context.

Saved items can be edited, suspended, resumed, dismissed/restored, deduplicated, and deleted. The due-review queue reveals the answer before the learner rates recall as Again, Hard, Good, or Easy. A small deterministic local interval scheduler stores due dates and review history in SQLite. It is intentionally not FSRS and does not claim measured learning gain.

The feature uses additive SQLite tables and the existing FastAPI/plain JavaScript stack. It requires no account, paid service, external model, or hosted infrastructure. See [the Product Roadmap](docs/PRODUCT_ROADMAP.md) and [Phase D acceptance checklist](docs/ACCEPTANCE_CHECKLIST.md). Implementation and acceptance status are tracked separately in [Current State](docs/CURRENT_STATE.md).


## Career & Interview Studios (Phase E)

The Career workspace adds three authored interview studios: project explanation, HR/behavioural interviews, and technical fundamentals. Each has four main questions and a relevant follow-up for every answer. Guided, standard, and challenging modes select different authored follow-up wording.

Answers can be typed or recorded and transcribed through the existing optional voice layer. Transcripts remain editable; prompts can be spoken with the existing TTS adapter. If Groq Whisper is configured, the interface discloses remote audio processing before requesting microphone access. Prepped does not store raw recordings.

Completed interviews show question-by-question formative reflection with the original answer and transparent text signals. This is not a technical correctness grader, recruiter evaluation, or placement predictor. Sessions are stored locally, can be resumed/retried/deleted, and a learner can explicitly send an answer to the Phase D memory editor for review before saving.

The studio content is versioned in `content/career-studios.v1.json`. API routes are under `/api/career`. No paid service, account, remote LLM interviewer, or additional infrastructure is required. The recorded pre-Phase-H full-suite CI baseline: [112 passed, 2 skipped, 1 warning](https://github.com/Exploiter69/Prepped/actions/runs/44721637341); the two skips require `espeak-ng`. Target-device microphone/TTS and responsive acceptance remain manual checks; see [the acceptance checklist](docs/ACCEPTANCE_CHECKLIST.md).


## Progress, goals, and portability (Phase F)

The Progress workspace combines saved activity with source-linked skill evidence, project-practice sessions, Career interviews, learner-approved memory reviews, due revision, recent activity, and daily/weekly plans. Authored closed-exercise outcomes are separated from open self-review and practice activity. The HR/behavioural and technical interview skills are mapped to active Career Studios, so learners can practise them through the Career workspace rather than duplicate lesson pages. No proficiency score or prediction is produced.

Learners can create, edit, archive, restore, and delete goals for completed lessons, project-practice sessions, interviews, and memory reviews. Goal counts begin when the goal is created. Recommendations explain whether they are based on a saved profile route, an unfinished lesson, due memory notes, or an active goal. You can dismiss a suggestion and restore it later; that choice is saved locally and included in backups.

The same workspace can export a local JSON backup and restore it after explicit confirmation. It includes the learner profile, practice answers, lesson attempts/events, memory notes/reviews, interview sessions/turns, goals, and dismissed recommendation preferences, plus adaptive daily plans and plan items. Restore is a full replacement, not a merge; the app validates the backup in a temporary database before replacing current data. Schema-3 backups remain restorable and are migrated with empty adaptive-plan tables. Backups are unencrypted and contain personal content; keep them private. Current limit: 25 MiB / 200,000 records, backup format version 1 and database schema version 4.

The app is designed for single-user loopback use. Run it on 127.0.0.1 only; it has no authentication or multi-user isolation and must not be exposed to a LAN or public internet. See [the release hardening record](docs/RELEASE_HARDENING.md) and [the clean install/recovery guide](docs/INSTALL.md).

## Adaptive learning intelligence (Phase H)

The Progress workspace now includes an evidence-backed learner skill profile, explainable deterministic next steps, daily and weekly learning plans, and source-linked activity analytics. It derives skill states from existing curriculum and saved records rather than maintaining a duplicate skill database. Authored closed-exercise outcomes are separated from open self-review, project practice, Career activity, and learner-rated memory revision.

Learners can generate a daily plan or seven-day plan, set a time budget, add lessons/interview/project practice, reorder or skip suggestions, and see completion only when the linked source activity is saved. Recommendations use repeated closed-exercise review needs, prerequisites, profile routes, due revisions, and active goals. The implementation adapts sequence and selection only; the curriculum has no difficulty metadata, so no difficulty scoring or generated exercises are claimed.

This is deterministic local adaptation, not an AI tutor, proficiency assessment, or validated learning model. See [Phase H implementation and acceptance gates](docs/PHASE_H_ACCEPTANCE.md). Automated CI is green: [134 passed, 2 optional skips, 1 warning](https://github.com/Exploiter69/Prepped/actions/runs/44732997261). Manual Omarchy and learner acceptance remain outstanding.


Progress is evidence of saved activity, not proficiency, learning gains, confidence measurement, hiring likelihood, or placement prediction. The optional student usability pilot has not been run; no results are claimed.
