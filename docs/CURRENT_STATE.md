# Prepped — Current State

**Updated:** 2026-11-20<br>
**Source of truth:** GitHub `feature/learner-profile` (working branch; `main` remains the last synced baseline)<br>
**Product direction:** Voice-first, personalised practice and learning platform for Indian engineering students. The text practice loop is a reliable fallback and is frozen for feature development except material bugs.<br>
**Engineering stage:** Phases A–H implementation is present. Phase I implementation is present; local pytest on commit `c4200e5` reports 145 passed, 0 failed, 1 warning. Exact-commit GitHub Actions [run 44742961672](https://github.com/Exploiter69/Prepped/actions/runs/44742961672) passed with 143 passed, 2 optional voice skips, 1 warning. Manual target-device acceptance remains pending. By explicit user decision, Phase J implementation is proceeding while Phase I remains open. See [Phase I acceptance](PHASE_I_ACCEPTANCE.md) and [Phase J acceptance](PHASE_J_ACCEPTANCE.md).

## Phase K — Security, Privacy, Data Protection & Reliability (engineering implementation and CI passed; local/manual acceptance open)

Phase K implementation is on commit f0d4dd14673392ea90787a7029873be11f89b69b. GitHub Actions [run 44750831526](https://github.com/Exploiter69/Prepped/actions/runs/44750831526) passed with 168 passed, 2 skipped, and no warnings. pip-audit found 0 known vulnerabilities across 73 resolved dependencies; the 68-entry licence inventory was reviewed. It records Vosk Apache, optional Piper GPL-3.0-or-later, and the local prepped package as UNKNOWN because the repository has no project licence declaration.

Implemented controls include actual TCP-peer loopback enforcement, bounded request bodies, private SQLite file permissions and symlink rejection, safe voice error handling, rollback/disk-full/permission/migration/deletion/provider-timeout/log-redaction tests, threat model and personal-data inventory, backup encryption decision, and CI vulnerability/licence artifacts. User laptop tests and disposable-data disk/permission/interrupted-restore rehearsals remain open. No security certification or public deployment approval is claimed. Do not redistribute until the owner selects a project licence and reviews optional Piper terms.

See [Phase K Acceptance](PHASE_K_ACCEPTANCE.md) and [Release Hardening](RELEASE_HARDENING.md).

## Phase J — Curriculum Quality, Content Expansion & Learning Validation (implementation started; acceptance pending)

The initial inventory found 14 lessons, 14 skills, 4 tracks, 9 units, and 49 exercises across seven exercise types. Four interview-related skills are mapped to existing Career Studios rather than duplicated as lessons. Phase J implementation now includes source registers, explicit completion conditions, review disclosure, cross-file skill coverage validation, a CI/startup content linter, and exercise-level outcomes, effort estimates, and inherited lesson skill/source context for all 49 exercises. The loader and regression tests enforce these exercise metadata rules and lesson effort budgets. Exact-commit automated verification of this latest slice is pending; human subject-matter review, accessibility review, manual journeys, and learner validation remain open.

See [Phase J Acceptance](PHASE_J_ACCEPTANCE.md) and [Content Review Log](CONTENT_REVIEW_LOG.md).

## Phase I — Voice Intelligence & Contextual Coaching (implementation added; acceptance pending)

The current branch now includes the first complete Phase I implementation slice:

- Browser TTS requests and in-flight STT transcription requests are abortable in the Project Practice voice controller. Workspace cancellation increments the request generation, aborts outstanding fetches, stops active recording streams, and ignores stale results.
- Career Studio TTS and STT requests have request identity, AbortController cancellation, object-URL cleanup, and stale completion guards. Leaving Career, changing prompt, stopping playback, or unloading the page cancels pending synthesis or transcription.
- Career curriculum version 1.2.0 adds an authored contextual follow-up rule, simpler wording, and clarification hint for each primary question/follow-up across Project Explanation, HR/Behavioural, and Technical Fundamentals. Deterministic text-cue rules choose a contextual prompt or the existing difficulty-specific fallback; the UI explains the cue and its limitations.
- Career feedback now includes one response-specific next action per turn, grounded in the saved answer excerpt and explicit cue limitations. A retry review compares prior/current answer text side by side without claiming measured improvement. It remains formative reflection, not correctness grading or a score.
- Learners can explicitly save a coaching action to existing Learning Memory or add the next studio practice to the existing daily adaptive plan. No new table or migration was added.
- Text answers, editable transcripts, existing saved session snapshots, history, retries, deletion, existing Memory, and adaptive-plan semantics remain in place.
- Automated tests were added for authored contextual prompt selection, simpler wording/hints, retry comparisons, feedback coaching, adaptive-plan handoff, and Career/Project TTS and STT cancellation on workspace navigation. Exact-commit CI has not yet been recorded.
- Manual target-laptop microphone, STT/TTS, privacy, accessibility, and end-to-end plan/Memory acceptance remain open.

**Important limitations:** cue selection and coaching use transparent lexical heuristics and can miss equivalent wording or match weak answers. They do not verify technical correctness, assess proficiency, score pronunciation, infer emotion/personality, or predict hiring/placement. Voice remains push-to-talk and turn-based; no always-listening or realtime speech agent was added.

## Phase G — release hardening implemented; device acceptance open

The current working branch now includes:
- Strict Host authority parsing and same-origin scheme/authority validation, with controlled 400/403 responses for malformed values.
- Backup restore validation for non-finite/out-of-range numbers, excessive JSON nesting, invalid Content-Length, and the 200,000-record cap; failed validation preserves the active database.
- Readiness regression coverage for missing required tables.
- Expanded security-header, no-store, and no-CORS checks.
- Static checks against unsafe HTML string sinks, Git ignore coverage for private local data and exported backups, and contrast checks for core dark-theme text/status tokens.
- Browser acceptance for keyboard-only focus/navigation, profile labels, and 375 px viewport overflow across the main workspaces.
- A dedicated [Phase G acceptance record](PHASE_G_ACCEPTANCE.md). Final automated CI verification is green; target-device checks remain pending.

## Foundation and A–F automated verification

- GitHub Actions now runs on `feature/**`, including this working branch, and on pull requests targeting `main` or `feature/learner-profile`.
- The workflow performs a clean checkout, installs `.[dev,browser-test]`, compiles Python modules, checks both browser JavaScript files, installs Chromium, and runs pytest including the Playwright browser journeys.
- Latest full CI: [GitHub Actions run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261) — **134 passed, 2 skipped, 1 warning** on commit ba5d4091c3679afe6b261852ca87f2940ba40877. Python compilation, seven JavaScript syntax checks, dependency consistency, `pip-audit`, Chromium setup, API tests, and browser acceptance passed. The two skips require `espeak-ng`, unavailable on the hosted runner; the pytest warning is Starlette's httpx-backed TestClient deprecation.
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

**Validation status:** The current full-suite GitHub Actions run [44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) passes 112 tests with 2 optional `espeak-ng` skips and 1 warning. This includes the profile journeys; target-laptop manual acceptance remains outstanding.

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

## Historical verification of the uploaded snapshot (2026-11-04)

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

## Voice-specific evidence and target-device checks still outstanding

- A real browser microphone session using Groq on the target machine: permission prompt, record/stop, transcript insertion, editing, submission, TTS play/stop/replay, and restart persistence. The provider adapter is covered by mocked tests, not a live API call.
- Speech-recognition accuracy or word-error rate on representative Indian English speech with either provider. No such result is claimed.
- A repeatable latency/memory benchmark across repeated runs and devices.
- A clean install and full manual recovery rehearsal on the target Omarchy laptop; the hosted CI clean-checkout run does not replace this device check.
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

## Product status and next build sequence (2026-11-20)

### Honest product status

Prepped is **not yet a complete or market-ready learning platform**. It is a local-first practice and learning application with a project-explanation scenario, an English curriculum, a voice record/stop slice, session history, formative feedback, and a learner profile.

The learner profile stores preferences such as goal, study year, branch, confidence, and focus areas. The goal and focus areas now select an explainable starter route through the Learning Engine and English curriculum. They do not infer ability, adapt difficulty, or certify proficiency.

### Implemented on the working branch

- **A — Foundation:** profile, original practice loop, and bounded voice record/stop slice.
- **B — Learning Engine:** versioned curriculum, lesson runner, exercises, progress events, and transparent profile-based routes.
- **C — English and communication:** authored foundations curriculum, listening, speaking, and pronunciation self-review.
- **D — Learning memory:** learner-approved notes, source evidence, duplicate handling, and local review scheduling.
- **E — Career studios:** project, HR/behavioural, and technical interview practice with follow-ups.
- **F — Progress and portability:** activity evidence, goals, explainable recommendations, local backup/restore, and initial operational hardening controls.

### Remaining before local release-candidate sign-off

1. Complete the target-Omarchy manual acceptance in [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md): Learning, memory/review, all Career studios, Progress/goals, backup/restore, voice permission/disclosure, keyboard/screen-reader, contrast, and responsive behaviour.
2. Record fresh-install and recovery results on the target laptop. Keep the backup/restore test on disposable data.
3. Review the known single-user loopback, unencrypted-backup, optional-Groq, and voice-engine limitations; do not expose the app publicly.
4. Run the optional consent-based student pilot only when participants are available. It is not an engineering blocker and has no results yet.

Phase G engineering is implemented; target-device acceptance remains open. The final automated gate and target-device release acceptance are tracked in [PHASE_G_ACCEPTANCE.md](PHASE_G_ACCEPTANCE.md).

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
- Profile-driven Learning routes cover English fluency, placement interviews, project communication, and professional communication. The Learning recommendation for technical-interview goals still points to project-explanation foundations; the separate Career workspace now provides a technical fundamentals interview studio.
- Learning workspace UI for the skill map, levels/units, recommended tracks, the optional baseline check/history, all seven exercise formats, local TTS listening/pronunciation playback with revealable text alternatives, optional STT spoken responses, feedback, next-lesson navigation, progress, and resuming unfinished lessons.
- Choice, vocabulary, listening, and ordering feedback compares a response to authored answer keys. Short responses are saved for learner self-review with an illustrative example and are never automatically graded. No overall or proficiency score is generated.

**Automated verification:** included in [the latest green CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341), with API and Chromium learning journeys passing. Target-laptop browser/responsive acceptance remains a separate manual check.

### Phase B boundaries

Phase B provides the reusable learning foundation, not advanced adaptive instruction or a validated assessment. The expanded initial English path is documented separately under Phase C. The low-stakes starting-point check stores choice, ordering, listening, and short-response evidence, supports repeat/review, and does not assign a proficiency level or score.

## Phase C — English and communication studio implementation update

**Implementation added; automated coverage passes in the latest CI run. Target-device acceptance remains pending.**

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

**Automated coverage added:** curriculum coverage and validation, profile-focus recommendation reasons, article/tense/question/vocabulary answer handling, listening text alternatives, pronunciation self-review feedback, and Chromium flows for the expanded track, listening conversations, and pronunciation. These tests passed in [the latest CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341).

**Manual acceptance still required:** target-laptop browser review of all units, TTS replay, microphone permission and optional STT disclosure, transcript correction, text fallback, keyboard use, and narrow-screen layout. No speech-recognition accuracy or learning-outcome claim is made.

### Voice configuration observation (2026-11-19)

The user confirmed GET /api/voice/status reports groq-whisper / whisper-large-v3 available and local Piper en_US-lessac-medium available. This verifies configuration visibility, not live transcription quality or a measured Indian-English word-error rate. Audio sent to Groq leaves the device; Prepped does not persist raw audio by default.


---

## Phase D — Personal learning memory and revision (2026-11-19)

**Implementation status: added on `feature/learner-profile`; the complete current suite passes in [CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341); target-device manual acceptance remains pending.**

CI evidence: [run 44561847713](https://github.com/Exploiter69/Prepped/actions/runs/44561847713). The two skips require `espeak-ng`, which is not installed on the hosted runner.

The Learning workspace now includes a local personal memory and spaced-revision area:

- Explicitly saved words, phrases, corrections, concepts, and examples.
- Lesson and project-practice feedback suggestions that prefill an editor; no suggestion is persisted without learner submission.
- Source metadata and quoted evidence for lesson- and practice-derived items.
- Edit, suspend/resume, dismiss/restore, duplicate resolution by opening the existing item for editing, and permanent delete with review-history cascade.
- Due queue with reveal-before-rating and Again / Hard / Good / Easy actions.
- A small transparent local interval scheduler with review history, lapse/repetition counts, and persisted due dates. It is not FSRS.
- Additive `learning_memory` and `learning_memory_reviews` tables. Existing session, answer, profile, and learning attempt/event tables are preserved.

GitHub Actions passes on the final Phase D implementation: 79 passed, 2 skipped (both require `espeak-ng`), including API coverage for CRUD, validation, duplicate detection, source retention, scheduler behaviour, history, deletion, restart persistence, legacy data, and Chromium memory journeys.

No mandatory paid service, external model, raw audio storage, login, or new infrastructure was added. Target-laptop manual acceptance remains outstanding.


---

## Phase E — Career & Interview Studios (2026-11-19)

**Implemented on `feature/learner-profile`; the complete current suite passes in [CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341); target-laptop acceptance pending.** Phase D target-laptop acceptance remains a separate open gate.

The Career header entry opens a local workspace with three studios:

- Project Explanation Studio.
- HR & Behavioural Interview Studio.
- Technical Interview Studio covering selected CS fundamentals.

Each studio currently contains four authored main questions. Every main question has one authored follow-up; guided, standard, and challenging modes select distinct follow-up prompts. The session API persists ordered turns and a versioned content snapshot. In-progress interviews can be resumed; completed interviews can be reviewed, retried, or deleted.

The browser supports typed answers, optional record/stop capture through the existing STT endpoint, editable transcripts, and spoken prompts through the existing TTS endpoint. If Groq Whisper is configured, the Career microphone action discloses that the recording will be sent to Groq before requesting microphone permission. Prepped does not persist raw audio. Text answers remain available.

Review is formative and transparent: it displays each original answer, simple response-development/example/reasoning signals, and suggestions. It does not check technical correctness, assign an interview score, or predict hiring outcomes. A learner may explicitly send an answer to the Phase D memory editor; it remains an editable suggestion until saved.

New additive SQLite tables: `career_sessions` and `career_turns`. Existing practice sessions, answers, learner profile, learning attempts/events, and memory tables are preserved. No paid service, new infrastructure, mandatory model, or remote LLM feedback was added.

**CI evidence:** the current full-suite run [44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) passes 100 tests with 2 optional `espeak-ng` skips and 1 warning, including Career API and Chromium coverage. **Manual verification still required:** target-laptop text-mode completion across all studios; microphone permission and local/Groq disclosure paths; TTS playback where available; session resume/retry/delete; memory handoff; keyboard and narrow-screen acceptance. Do not mark Phase E fully accepted until device checks are recorded.


---

## Phase F — Progress, portability, and hardening foundations (2026-11-19)

**Implementation added on `feature/learner-profile`; [final automated CI is green (112 passed, 2 skipped)](https://github.com/Exploiter69/Prepped/actions/runs/44721637341). Target-laptop manual acceptance remains pending. Phase D and Phase E device checks remain separate open gates.

### Progress and goals

- New `/api/progress/overview` combines completed lesson evidence by curriculum skill, project-practice sessions, career interview sessions, memory review counts, due notes, active goals, seven-day activity, recent activity, and explainable next steps.
- Skill progress is linked to completed lesson events and the curriculum's declared skill IDs. It reports lesson coverage and evidence titles only; it is not a skill-proficiency score. The baseline diagnostic is excluded from lesson completion counts.
- Learner-owned goals support lessons completed, project practice sessions, interviews completed, and memory reviews. Learners can dismiss and restore explainable next-step recommendations; these preferences persist and are included in backups. Create, edit, archive/restore, and delete are available. Counts start at each goal's creation timestamp; existing activity is not silently credited to a newly created goal.
- Recommendations are deterministic and explain their source: resume an unfinished lesson, project-practice session, or interview; review due learner-saved notes; continue the next lesson in the profile-selected route; or work toward an active goal.

### Export, backup, restore, and recovery

- New `/api/data/status`, `GET /api/data/export`, and `POST /api/data/restore` endpoints.
- Progress workspace can download a JSON backup and select a local backup for restore.
- The versioned backup contains all current learner-data tables: `learner_profile`, `sessions`, `answers`, `learning_attempts`, `learning_events`, `learning_memory`, `learning_memory_reviews`, `career_sessions`, `career_turns`, `learner_goals`, and `recommendation_dismissals`.
- It does not include source code, environment variables, API keys, or voice models.
- Restore requires an explicit confirmation and replaces all current learner data; it is not a merge. Request size is capped at 25 MiB and records at 200,000.
- Restore first rebuilds the data in a temporary database using the current additive schema, validates exact tables/columns and scalar fields, checks constraints, SQLite integrity, and foreign keys, then copies the validated database into place. Invalid backups leave the current database unchanged.
- Backup format version and database schema version are explicit (format version 1, database schema version 4). Dismissed recommendation preferences and adaptive plans are part of the backup; schema-3 backups are migrated with empty adaptive-plan tables. Incompatible versions fail closed.
- Backups are unencrypted JSON and contain personal answers and notes; users must keep them private.

### Release hardening

- The application accepts loopback Host names only and rejects cross-origin state-changing requests when an Origin header is present.
- Added CSP, frame denial, MIME sniffing protection, restrictive referrer and permissions policies, same-origin resource/opener policies, and `Cache-Control: no-store` on API responses.
- Added `/api/ready` to check SQLite quick integrity, required Phase A–H tables, and curriculum loading.
- CI now checks `static/progress.js` and `static/intelligence.js`, runs API and Chromium acceptance, and performs a Python dependency audit with `pip-audit`.
- Added [clean install, supported environment and recovery guide](INSTALL.md) and [release hardening/security record](RELEASE_HARDENING.md).

### Verification still required

- **Automated:** final GitHub Actions run for the exact Phase F commit, including dependency audit, compilation, all JavaScript syntax checks, API tests, and Chromium progress/backup journeys.
- **Target device:** fresh install on Omarchy; check progress numbers against saved records; create/edit/archive/restore/delete goals; backup and restore every data category; verify an invalid backup leaves current data intact; keyboard-only and screen-reader labels/status; focus, contrast, and narrow-screen layout.
- **Existing phases:** Phase D memory and Phase E interview journeys still need their own target-laptop acceptance. CI does not prove microphone permission, live transcription quality, local Piper/espeak playback, or device-specific behaviour.
- **Usability validation:** the optional student pilot has not been run. No sample size, participant results, learning gains, or placement outcomes are claimed.

### Scope and limitations

Prepped remains a local single-user loopback application with no authentication or multi-user isolation. Do not expose it on a LAN, public internet, reverse proxy, or tunnel. Progress is saved-activity evidence, not proficiency or learning gain. Backups are not encrypted and support backup format version 1 with database schema version 4. Schema-3 backups are migrated to schema 4 with empty adaptive-plan tables. See [INSTALL.md](INSTALL.md), [RELEASE_HARDENING.md](RELEASE_HARDENING.md), and [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md).


## Phase G.1 — recording lifecycle hardening (implementation and CI green)

Learning and Career recording now invalidate pending microphone permission requests when leaving the relevant workspace. Late permission grants are discarded with their tracks stopped; active streams are released on workspace changes; in-flight transcription is abortable and stale callbacks are ignored. Deferred-permission Playwright regressions for both Learning and Career passed in [CI run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261). Manual Omarchy microphone acceptance is still deferred.

## Phase H — Adaptive Learning Intelligence (implementation and CI green; manual acceptance pending)

- H1: derived skill evidence across active curriculum skills, lesson attempts, closed-exercise responses, open self-review, project/Career activity, and source-linked learner-approved lesson, project-practice, and Career memory reviews. HR/behavioural and technical Career skills with planned curriculum content are shown as practice-only evidence. Freshness and evidence coverage are visible; no mastery/proficiency score is assigned.
- H2: deterministic, source-explained recommendations use repeated closed-exercise review needs, prerequisites, profile routes, due revisions, and active learner goals. Learners can dismiss/restore recommendations and override by choosing activities.
- H3: persisted daily and seven-day plans combine due reviews, suitable lessons, and optional interview/project practice. Learners control time budget, additions, reordering, skipping, and regeneration. Completion is derived from linked saved activity.
- H4: per-skill evidence timelines, 30-day activity history, revision ratings, repeated review signals, and source-linked analytics.
- Additive tables: adaptive_plans and adaptive_plan_items. SQLite schema version 4. Existing schema-3 backups remain restorable and initialise the new plan tables empty.
- New APIs are under /api/intelligence; the learner-facing workspace is integrated into Progress. See [Phase H Acceptance](PHASE_H_ACCEPTANCE.md).

**Verification:** API, browser, backup/restore, sparse/conflicting/stale evidence, prerequisite, repeated-error, active-goal, and plan controls tests have been added. Automated CI is green on the implementation commit: [run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261). Target-device acceptance and learner validation remain separate later gates.

## Remaining product acceptance

Phase A–G manual target-laptop checks remain open, including microphone/STT/TTS, recovery rehearsal, keyboard/screen-reader review, contrast, and narrow-screen behaviour. Phase H needs its own manual review after CI. The student usability pilot has not been run; no learning-gain or placement-outcome claims are made.
