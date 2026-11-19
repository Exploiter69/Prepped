# Prepped

**Prepped is a local-first, voice-enabled practice environment for Indian engineering students working on placement preparation, professional communication, English fluency, and technical interview practice.**

The product direction is **voice-first and personalised over time**. The existing text practice loop remains the reliable fallback. Voice supports record/stop capture, an editable transcript, and spoken interviewer prompts. Speech recognition can run locally with Vosk or, when explicitly configured, through Groq Whisper for stronger multilingual transcription.

This repository does **not** claim validated speech accuracy, placement improvement, or an AI interviewer. No paid service is required. Optional Groq transcription sends recordings to Groq; without a Groq key, the app uses local Vosk.

## Start here

- [Current implementation and verification status](docs/CURRENT_STATE.md)
- [Foundation browser and data acceptance checklist](docs/ACCEPTANCE_CHECKLIST.md)
- [Voice setup, privacy, and troubleshooting](docs/VOICE.md)
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

**Explain your project to a placement interviewer.** The learner answers five prompts about the problem, personal contribution, a design decision, evidence, and reflection. Answers can be typed or spoken. Spoken answers are transcribed into an editable text box (locally with Vosk, or remotely with Groq when explicitly configured), then submitted through the same session API as typed answers. The UI discloses which transcription mode is active before recording. After the final answer, Prepped shows question-by-question notes and a transparent checklist, then supports retry, attempt comparison, local history, and deletion.



## Learning workspace — Phase B starter engine

The Learning entry in the header opens a reusable lesson workspace built on the same FastAPI + SQLite + plain JavaScript stack. The current versioned curriculum includes a stable skill map, goal-based tracks, prerequisites, examples, and six starter lessons grouped into six units across English foundations and project communication.

The lesson runner supports:
- Single-choice and contextual vocabulary exercises.
- Sentence/idea ordering.
- Listening comprehension using the configured local TTS endpoint, with a revealable text alternative.
- Short written or spoken responses. Spoken responses use the existing STT endpoint; Groq use is disclosed before recording, and raw audio is not stored by Prepped.
- Deterministic answer feedback for closed exercises; open responses are saved for learner self-review and are not automatically graded.
- Ordered attempts, prerequisite enforcement, restart-safe resume, and progress events.

The saved learner goal and focus areas select an explainable starter route. The optional Starting point check records a few sentence, listening, and project-response tasks for later comparison. It can be repeated and reviewed; it assigns no proficiency level or total score. The progress view reports recorded activity counts, not proficiency or learning gains. The curriculum is intentionally a starter slice; broader grammar, vocabulary, listening, pronunciation, advanced diagnostic interpretation, revision, and interview content remains on the roadmap.

Learning API: GET /api/learning/catalog, GET /api/learning/recommendations, POST /api/learning/attempts, GET /api/learning/attempts/{id}, POST /api/learning/attempts/{id}/responses, GET /api/learning/progress, and GET /api/learning/diagnostic/latest.

## Run locally

Requires Python 3.11 or newer. The voice slice also uses `ffmpeg` to decode browser recordings and a local speech model. Text mode works without either.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,voice,voice-cloud]"
python -m uvicorn prepped.main:app --reload
```

Open `http://127.0.0.1:8000`. The health endpoint is `/api/health`; the scenario definition is `/api/scenarios/project-explanation`; voice provider availability is `/api/voice/status`.

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
- No LLM feedback, adaptive intelligence, pronunciation scoring, or emotion/personality inference is added in this phase.

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

## Current status

The text practice loop is implemented on `main`. The voice slice has modular Groq Whisper and Vosk STT adapters, Piper/espeak TTS adapters, browser record/stop controls, editable transcripts, and text fallbacks. The Groq adapter has mocked automated tests; a live provider call and target-laptop browser acceptance are still outstanding. See [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).
