# Prepped — Current State

**Updated:** 2026-11-19<br>
**Source of truth:** GitHub `feature/learner-profile` (working branch; `main` remains the last synced baseline)<br>
**Product direction:** Voice-first, personalised practice and learning platform for Indian engineering students. The text practice loop is a reliable fallback and is frozen for feature development except material bugs.<br>
**Engineering stage:** Phase B Learning Engine and Phase C English/Communication curriculum implementations are on the working branch; the latest automated validation must pass before those milestones are called automated-tested. Target-laptop browser, microphone, and live-provider acceptance remain.

## Foundation acceptance — automated checks and CI passing

- GitHub Actions now runs on `feature/**`, including this working branch, and on pull requests targeting `main` or `feature/learner-profile`.
- The workflow performs a clean checkout, installs `.[dev,browser-test]`, compiles Python modules, checks both browser JavaScript files, installs Chromium, and runs pytest including the Playwright browser journeys.
- Latest recorded run: [GitHub Actions run 44534499386](https://github.com/Exploiter69/Prepped/actions/runs/44534499386) — **41 passed, 2 skipped, 1 warning**. Both skips are voice tests requiring `espeak-ng`, which is not installed on the hosted runner. The warning is Starlette's deprecation notice for the httpx-backed TestClient.
- A repeatable [Foundation Acceptance Checklist](ACCEPTANCE_CHECKLIST.md) now covers profile setup/edit/cancel/save/reload, existing text practice, optional voice acceptance, and data preservation. Playwright/Chromium browser tests now exercise profile open, save, edit, cancel, reload and persistence, plus the complete text-only practice flow without a profile. These tests passed in CI. The target-laptop browser and voice/microphone checks remain separate manual acceptance.
- Headless Chromium confirms the profile and text-practice interactions in CI. A manual spot check on the target Omarchy laptop and microphone/STT/TTS acceptance remain outstanding; CI does not establish hardware or device acceptance.

## Learner workspace — profile implemented; automated browser acceptance passing

The `feature/learner-profile` branch now contains:
- `docs/PRODUCT_ROADMAP.md` defining the full product modules, delivery sequence, architecture constraints, and quality gates.
- Additive SQLite `learner_profile` table; existing session and answer tables are not dropped or rewritten.
- `GET /api/profile` and `PUT /api/profile` endpoints for one local profile.
- Server-side validation for study year, goal, confidence level, text lengths, and improvement-area choices.
- Profile setup/edit UI with optional name, study year, branch, target role, primary goal, confidence, and improvement areas. Profile setup can be skipped; the existing practice flow is not gated.
- `tests/test_profile.py` covering initial state, save/read, updates, restart persistence, invalid input, and legacy session/answer preservation.

**Validation status:** The latest GitHub Actions run completed successfully: 41 passed, 2 skipped, 1 warning. The two skips require `espeak-ng`, unavailable on the hosted runner. Playwright/Chromium exercised profile setup, open/close, save, edit, cancel, reload/persistence, and the full text-only practice flow without a profile. The profile milestone has automated browser acceptance; a target-laptop manual spot check is still outstanding.

## What this milestone is

The voice milestone is a **record/stop** flow inside the existing project-interview scenario, not a realtime always-listening agent. STT can use optional Groq Whisper or local Vosk:

1. The existing text scenario remains available.
2. The learner presses **Start recording**, speaks, and presses **Stop recording**.
3. The browser sends the recording to the local FastAPI app.
4. `ffmpeg` decodes it in memory. Groq Whisper transcribes it when `GROQ_API_KEY` is configured; otherwise local Vosk is used.
5. The transcript is placed in the existing editable answer box.
6. The learner corrects recognition errors and saves through the **existing** answer endpoint.
7. Interviewer prompts can be spoken with local TTS, with **Play**, **Stop**, and **Replay** controls.
8. Microphone/model/TTS failures keep text mode usable.

## Implemented

### Existing text loop (kept)

- One versioned project-explanation scenario with five prompts and a versioned rubric.
- FastAPI backend with a plain HTML/CSS/JavaScript interface.
- SQLite local session storage and additive migrations.
- Ordered answer capture, empty-answer handling, cancellation, completion, and answer-length limits.
- Deterministic feedback with evidence excerpts, prompt-specific next actions, explicit uncertainty, and no overall score.
- Retry with scenario/rubric snapshot, attempt grouping/comparison data, local history, and session deletion.
- Regression tests for core flow, feedback grounding/limitations, empty answers, cancellation, boundaries, retry, history, and deletion.
- No mandatory AI account, paid API, hosted database, or raw audio capture. Groq transcription is optional and only active when the developer configures a server-side key.

### Voice slice (new)

- `prepped/voice/` package with replaceable STT/TTS interfaces:
  - `SpeechToTextEngine` / `TextToSpeechEngine` protocols.
  - `VoskSTT` local speech-to-text adapter and opt-in `GroqWhisperSTT` cloud adapter (`whisper-large-v3`).
  - `PiperTTS` local neural text-to-speech adapter.
  - `EspeakTTS` local fallback adapter.
  - `VoiceService` for limits, availability, privacy text, and engine coordination.
  - In-memory `ffmpeg` decoding to mono 16 kHz PCM; no temporary raw-audio files.
- Streaming request-size enforcement before the complete audio body is buffered; oversized requests are rejected with HTTP 413.
- Microphone permission requests are invalidated when the question/session changes; late permission grants have their tracks stopped rather than starting a stale recording.
- API endpoints:
  - `GET /api/voice/status` — engine availability, model names, limits, privacy/fallback text.
  - `POST /api/voice/transcribe` — raw audio body in, transcript JSON out, `stored_audio: false`.
  - `POST /api/voice/tts` — question text in, local WAV out with `Cache-Control: no-store`.
- Browser UI:
  - Microphone permission and **Start recording** / **Stop recording**, with provider-specific disclosure before capture.
  - 60-second recording cap and visible timer.
  - Transcription from the configured provider is inserted into the existing answer textarea for editing; Vosk runs locally, while Groq sends recordings to its service.
  - **Play question aloud**, **Stop**, and **Replay** controls.
  - Clear errors for denied/unavailable microphone, missing model, undecodable audio, and TTS failure.
  - Text mode remains visible and usable throughout.
- Tests:
  - Mocked API/engine boundary tests.
  - Missing-engine, empty/oversized/undecodable-audio, and TTS-failure tests.
  - Text-mode regression when both voice engines are unavailable.
  - Real `espeak-ng` WAV synthesis test (skipped if not installed).
  - Opt-in real Vosk integration test from synthesized speech through decode + transcription (skipped if the model is not installed).

## Engines and licensing verified on 2026-11-04

| Component | Choice | License | Local footprint | Why |
|---|---|---|---|---|
| STT (optional cloud) | Groq `whisper-large-v3` | Hosted model | No local model download | Multilingual Whisper; free-tier access is rate-limited; audio leaves the device |
| STT (offline fallback) | Vosk 0.3.45 + `vosk-model-small-en-us-0.15` | Apache 2.0 | 40 MB compressed / 68 MB on disk | CPU-friendly, small, pip-installable, no cloud account |
| TTS (preferred) | Piper 1.8.0 + `en_US-lessac-medium` | GPL-3.0-or-later | 34 MB package + 61 MB voice | Better local speech, CPU-compatible |
| TTS (fallback) | `espeak-ng` | GPL-3.0 | Tiny system package | Zero-download fallback; robotic but functional |
| Audio decode | `ffmpeg` | LGPL/GPL build-dependent | System package | Decodes browser WebM/Opus/Ogg/MP4 in memory |

The old Piper repository is archived; current Piper development is at `OHF-Voice/piper1-gpl`. The pip package is GPL-3.0-or-later. It is an optional local process/dependency, not bundled into the repository. Vosk and the selected English model are Apache 2.0.

No model weights are committed. `models/` is ignored by Git. Model installation is explicit in `scripts/setup_voice.sh`; nothing is downloaded by application startup.

## Automated verification of the uploaded snapshot

Executed in an isolated Linux environment against the uploaded repository snapshot:

```text
$ python -m pytest -q
32 passed, 1 skipped in 0.62s
$ node --check static/app.js
$ node --check static/voice.js
$ python -m compileall -q prepped
```

The single skipped test is `tests/test_voice_integration.py`: `espeak-ng` is not installed in this audit environment. The Groq tests mock the HTTP response; no live API key or network call was used. This audit was performed against the uploaded snapshot, not the user's live laptop. The 32 passing tests use fake speech engines and a mocked Groq HTTP client for deterministic API and application checks; they do not prove a live Groq request, real microphone capture, real Vosk transcription, or real TTS playback.

### Previously recorded development-machine observations

The earlier development notes recorded the following on the Intel i5-1235U / Omarchy laptop: Vosk model load about 0.8 s; a synthetic ~4 s espeak sample decoded and transcribed in about 2.5 s; Piper model load about 4.5 s; one short prompt synthesized in about 0.43 s; process peak RSS about 190 MB. These are historical observations from the previous development session, not reproduced by this snapshot audit and not formal benchmarks. The notes also recorded an imperfect synthetic Vosk transcript. None of these observations establishes accuracy on representative Indian English speech.

## Not yet verified / outstanding

- A real browser microphone session using Groq on the target machine: permission prompt, record/stop, transcript insertion, editing, submission, TTS play/stop/replay, and restart persistence. The provider adapter is covered by mocked tests, not a live API call.
- Speech-recognition accuracy or word-error rate on representative Indian English speech with either provider. No such result is claimed.
- A repeatable latency/memory benchmark across repeated runs and devices.
- GitHub Actions result for this change. The local suite passes; CI must run on the pushed commit before merge.
- A fresh-checkout install/test/browser smoke test after this change.
- Student usability or voice-specific user validation. No pilot has been run and no results are claimed.

## Product development vs. future user validation

The student pilot is **not a blocker** for engineering development.

- **Engineering development:** building and testing the local voice slice, failure handling, text fallback, and maintainability.
- **Future user validation:** whether students understand the flow, whether transcripts are useful, whether spoken prompts help, and whether recognition errors are tolerable. This needs real participants and must be documented separately with sample size and limitations.

No pilot findings are fabricated or implied. A future voice-specific validation should add microphone-permission and transcript-correction tasks, with explicit consent for any remote-provider audio.

## Immediate commands

```bash
cd ~/Prepped-repo
source .venv/bin/activate
python -m pip install -e ".[dev]"
python3 -m pytest

# One-time explicit voice installation; not run at app startup
./scripts/setup_voice.sh

python -m uvicorn prepped.main:app --reload
```

Open `http://127.0.0.1:8000`.

Check voice availability:

```bash
curl -s http://127.0.0.1:8000/api/voice/status
```

Check spoken prompt synthesis:

```bash
curl -s -X POST http://127.0.0.1:8000/api/voice/tts \
  -H 'Content-Type: application/json' \
  -d '{"text":"Tell me about a project you have worked on."}' \
  --output /tmp/prepped-question.wav
```

If using Groq, export `GROQ_API_KEY` in the same terminal before starting Uvicorn. The default database is local at `data/prepped.sqlite3` and is ignored by Git. Do not put confidential interview content into the prototype. When using Groq, only send practice recordings you are comfortable transmitting to that provider.

## Product boundaries

Prepped is a practice prototype, not an official assessment, hiring decision, placement predictor, or validated speech-accuracy product. Feedback signals are simple text heuristics and can be wrong. Speech recognition can be wrong. There is no overall score, no pronunciation score, no emotion/personality inference, and no LLM feedback in this phase. Vosk mode stays local. Groq mode is an explicit remote transcription option. Raw audio is not retained by Prepped by default.

---

## Product status and next build sequence (2026-11-19)

### Honest product status

Prepped is **not yet a complete or market-ready learning platform**. It is a local-first practice and learning application with a project-explanation scenario, an English curriculum, a voice record/stop slice, session history, formative feedback, and a learner profile.

The learner profile stores preferences such as goal, study year, branch, confidence, and focus areas. The goal and focus areas now select an explainable starter route through the Learning Engine and English curriculum. They do not infer ability, adapt difficulty, or certify proficiency.

### Not implemented yet

- Learner-controlled vocabulary/correction memory and spaced revision.
- HR, behavioural and technical interview studios with multi-turn follow-ups.
- Evidence-based skill progress dashboard and goal tracking.
- Local export, backup and restore.
- Full release-grade accessibility, security, fresh-install and target-device acceptance.

### Active implementation order

Follow [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) and [COMPLETE_ROADMAP.md](COMPLETE_ROADMAP.md) as the detailed execution plan.

1. **Foundation acceptance:** verify profile setup/edit/save/reload and the existing practice/voice flows in a real browser; rerun automated checks and CI.
2. **Learning Engine:** complete automated and target-device acceptance of the implemented skill taxonomy, versioned JSON curriculum, reusable lesson runner, exercise types, progress events and profile-driven starter paths.
3. **English & communication studio:** implementation is on the branch; complete CI and target-laptop acceptance before closing Phase C.
4. **Personal learning memory:** learner-approved words, phrases, corrections and review cards with a transparent local scheduler.
5. **Career & interview studios:** project, HR/behavioural and technical tracks using shared scenario infrastructure.
6. **Progress & portability:** skill evidence, goals, explainable recommendations, export, backup and restore.
7. **Release hardening:** accessibility, security, responsive UX, fresh install, target-device acceptance and documented limitations.

### Profile toggle — automated browser acceptance passing

The explicit open/close helper, `aria-expanded` updates, and cache-busted assets are covered by Playwright/Chromium browser tests. The tests confirm setup opens, save closes, edit restores values, cancel discards unsaved changes, and saved preferences persist after reload. A manual spot check in the target browser is still outstanding; do not describe that device-specific check as complete.

### Release rule

A visible screen or saved profile is not a complete feature. Each module must have a full learner journey, persistence, validation, empty/error/retry states, automated tests, accessibility checks and manual acceptance. Keep the existing FastAPI + plain HTML/CSS/JavaScript + SQLite modular monolith, additive migrations, versioned JSON, ₹0 mandatory operating cost, and text fallback.

## Learning Engine — first vertical slice implemented; acceptance pending

The feature/learner-profile branch now includes the first Phase B implementation:

- Versioned local curriculum manifest at curriculum/curriculum.v1.json: 14 stable skills, one foundation level, nine units, four tracks, 13 authored lessons plus one diagnostic check, explicit learning outcomes, lesson prerequisites, examples, and seven exercise formats (choice, ordering, vocabulary, listening, short response, reflection, pronunciation).
- Curriculum validation for unique IDs, supported exercise types, answer/token integrity, and skill/track/lesson references. Invalid curriculum fails application startup rather than silently serving partial content.
- Reusable learning API: GET /api/learning/catalog (skill map, tracks, lessons, and profile-based route); GET /api/learning/recommendations; POST /api/learning/attempts; GET /api/learning/attempts/{id}; POST /api/learning/attempts/{id}/responses; and GET /api/learning/progress; GET /api/learning/diagnostic/latest (repeatable baseline snapshot and history).
- Additive learning_attempts and learning_events tables. Existing sessions, answers, and profile data are preserved.
- Profile-driven starting routes for English fluency, placement interviews, project communication, and professional communication. Technical-interview goals currently route through project-explanation foundations and disclose that the dedicated technical question bank is planned.
- Learning workspace UI for the skill map, levels/units, recommended tracks, the optional baseline check/history, all seven exercise formats, local TTS listening/pronunciation playback with revealable text alternatives, optional STT spoken responses, feedback, next-lesson navigation, progress, and resuming unfinished lessons.
- Choice, vocabulary, listening, and ordering feedback compares a response to authored answer keys. Short responses are saved for learner self-review with an illustrative example and are never automatically graded. No overall or proficiency score is generated.

**Validation in progress:** API tests and a Chromium end-to-end learning journey have been added, including reload/resume. The latest CI run must pass before this milestone is marked automated-tested. Target-laptop browser/responsive acceptance remains a separate manual check.

### Phase B boundaries

Phase B provides the reusable learning foundation, not advanced adaptive instruction or a validated assessment. The expanded initial English path is documented separately under Phase C. The low-stakes starting-point check stores choice, ordering, listening, and short-response evidence, supports repeat/review, and does not assign a proficiency level or score.

## Phase C — English and communication studio implementation update

**Implementation added; CI and manual target-device acceptance are pending.**

The English foundations path now contains 11 sequenced lessons across six units. The complete curriculum manifest has 14 stable skills, one foundation stage, nine units, four tracks, 13 authored lessons, and the separate baseline diagnostic. Every unit and lesson has explicit learning outcomes, and the lesson runner displays lesson outcomes before exercises.

Implemented content:

- **Sentence construction:** build complete sentences, expand, combine, shorten, and clarify without changing intended meaning.
- **Grammar in context:** past and future tense, articles, common prepositions, question formation, and authored explanations for answer choices.
- **Vocabulary:** precise word choice, collocations, phrase meaning, contextual examples, and learner-authored sentences.
- **Speaking fluency:** structured descriptions, process explanations, technical/project explanations, retelling, opinions, reasons, and follow-up responses. Text entry is always available; recording/transcription is optional.
- **Listening:** authored updates and short conversations with play/stop/replay controls, comprehension questions, and revealable transcript alternatives.
- **Pronunciation:** local TTS model phrases, listen-and-repeat activities, optional recording/transcription, and private self-review. There is no pronunciation, accent, phoneme, or fluency score.
- **Confidence and professional communication:** private repeatable practice and practical clarification/follow-up language. No emotion inference or automated confidence diagnosis.

The work reuses the existing versioned JSON curriculum, FastAPI lesson runner, SQLite attempt/event persistence, and plain JavaScript UI. No new paid service or infrastructure dependency was introduced. The original practice room and text-only route remain available.

**Automated coverage added:** curriculum coverage and validation, profile-focus recommendation reasons, article/tense/question/vocabulary answer handling, listening text alternatives, pronunciation self-review feedback, and Chromium flows for the expanded track, listening conversations, and pronunciation. These tests still require a successful latest CI run before they can be reported as passing.

**Manual acceptance still required:** target-laptop browser review of all units, TTS replay, microphone permission and optional STT disclosure, transcript correction, text fallback, keyboard use, and narrow-screen layout. No speech-recognition accuracy or learning-outcome claim is made.

### Voice configuration observation (2026-11-19)

The user confirmed GET /api/voice/status reports groq-whisper / whisper-large-v3 available and local Piper en_US-lessac-medium available. This verifies configuration visibility, not live transcription quality or a measured Indian-English word-error rate. Audio sent to Groq leaves the device; Prepped does not persist raw audio by default.


---

## Phase D — Personal learning memory and revision (2026-11-19)

**Implementation status: added on `feature/learner-profile`; automated CI and target-device acceptance pending.**

The Learning workspace now includes a local personal memory and spaced-revision area:

- Explicitly saved words, phrases, corrections, concepts, and examples.
- Lesson-feedback suggestions that prefill an editor; no suggestion is persisted without learner submission.
- Source metadata for lesson-derived items.
- Edit, suspend/resume, dismiss/restore, duplicate resolution by opening the existing item for editing, and permanent delete with review-history cascade.
- Due queue with reveal-before-rating and Again / Hard / Good / Easy actions.
- A small transparent local interval scheduler with review history, lapse/repetition counts, and persisted due dates. It is not FSRS.
- Additive `learning_memory` and `learning_memory_reviews` tables. Existing session, answer, profile, and learning attempt/event tables are preserved.

The current branch includes API tests for CRUD, validation, duplicate detection, source retention, scheduler behaviour, history, deletion, restart persistence, and legacy data, plus a Chromium memory journey test. These are coverage added, not proof of passing until CI completes on the final Phase D commit.

No mandatory paid service, external model, raw audio storage, login, or new infrastructure was added. Target-laptop manual acceptance remains outstanding.
