# Prepped — Product Roadmap

**Product direction:** A complete, local-first learning and career-readiness platform for Indian engineering students and early-career learners.

**Engineering principle:** Build a coherent product on the existing FastAPI + SQLite + HTML/CSS/JavaScript foundation. The existing practice room remains a working module. This roadmap expands it; it does not authorize a rewrite.

## Product promise

Prepped helps a learner become more capable at communicating, explaining technical work, learning English, and handling placement and early-career conversations through deliberate practice, feedback grounded in their own responses, review, and visible progress.

It is a practice and learning tool, not a hiring assessment, placement predictor, or substitute for a qualified teacher.

## Product modules

### 1. Learner workspace and personalisation
- One private local learner profile; no account or login requirement.
- Onboarding: current study year, branch, learning goals, confidence/starting level, target role, and focus areas.
- Editable preferences and goals.
- [Implemented] A low-stakes baseline diagnostic that records observable responses and completed tasks without claiming validated proficiency.
- Practice recommendations derived transparently from goals, recent activity, and observed evidence.
- Learner can skip onboarding and continue to the existing practice room.

### 2. Learning paths and skill map
- Skills grouped into English communication, professional communication, project explanation, interview readiness, and technical communication.
- Learning paths broken into small lessons, guided practice, and review.
- Clear prerequisite and progression rules; no opaque level score.
- Content stored as versioned local JSON so scenarios can be authored and reviewed without a CMS.

### 3. English and communication studio
- Everyday and professional English.
- Sentence construction, grammar-in-context, vocabulary, clarity, structure, conciseness, and confidence-building practice.
- Explain, summarise, describe, compare, clarify, ask questions, and give opinions.
- Pronunciation/listening exercises only where the installed local speech tools can support them; never invent accuracy scores.
- Corrections explain the issue and offer examples, not just a red/green judgement.

### 4. Interview and career studio
- Project explanation and personal contribution.
- HR and behavioural questions.
- Technical interview scenarios and concept explanations.
- Role- and domain-specific question sets.
- Follow-up questions and multi-turn mock interviews.
- Resume/project discussion practice can be added as a local document workflow later; no automatic hiring claims.

### 5. Voice-first tutor and practice room
- Spoken prompts, record/stop capture, editable transcripts, spoken playback, and text fallback.
- Local Vosk STT and Piper/espeak TTS remain the default direction.
- Optional provider adapters may be added only when explicitly configured; remote processing must be clearly disclosed.
- Voice failures never block text practice.
- No raw audio retention by default.
- Turn-based roleplay and scenario state are deterministic and testable before any optional generative tutor is introduced.

### 6. Personal learning memory and revision
- Save vocabulary, useful phrases, corrections, recurring mistakes, and weak concepts with learner consent/actions.
- Convert selected items into revision cards.
- Spaced repetition with a small, transparent local scheduler (FSRS-inspired only if implemented and tested; do not claim FSRS compatibility without it).
- Review queue, due dates, card editing, suspend/delete, and source context.
- Revisit errors in future practice without silently changing submitted answers.

### 7. Progress and insights
- Activity history and completed learning sessions.
- Progress by skill using explainable evidence and counts, not a misleading single score.
- Recurring patterns and recently practised topics.
- Review completion, consistency, and personal goals.
- Recommendations show why they were suggested and let the learner dismiss and restore them.
- Export/backup and restore of local learning data before broad use.

## Delivery sequence

### Foundation — Learner workspace (next)
1. SQLite learner profile with additive migration.
2. Profile read/update API and validation.
3. Accessible onboarding/edit interface; profile remains optional.
4. Tests for validation, persistence, and compatibility with existing sessions.

### Learning foundation
1. Skill taxonomy and versioned content manifest.
2. Scenario catalogue and reusable scenario runner.
3. [Implemented] Learner baseline diagnostic with transparent, non-certified output.
4. Rule-based recommendations connected to profile and practice history.

### Communication and interview studios
1. English micro-practice scenarios.
2. Professional communication and project explanation tracks.
3. HR/behavioural and technical interview scenario packs.
4. Multi-turn follow-up logic and mock-interview session review.

### Learning memory
1. Vocabulary/phrase and correction capture.
2. Mistake and weak-concept capture with explicit evidence/source.
3. Editable review cards and local spaced-repetition scheduler.
4. Review sessions integrated with learning paths.

### Progress and product hardening
1. Skill-level activity and evidence views.
2. Goal tracking and explainable recommendations.
3. Local data export/import and recovery.
4. Accessibility, responsive UX, security/privacy review, performance and fresh-install checks.
5. Documented manual acceptance on the target laptop and a small consent-based student usability study when available.

## Architecture and hard constraints

- Required runtime: Python 3.11+, FastAPI, SQLite, plain HTML/CSS/JavaScript.
- Existing app modules and session data must remain compatible; use additive database migrations.
- Keep a modular monolith and one SQLite database.
- ₹0 mandatory operating cost. No paid APIs, subscriptions, hosted database, or remote service as a required dependency.
- No mandatory login/accounts, React/Vue/Svelte, Redis, Kafka, Celery, Kubernetes, microservices, vector database, or second workflow engine.
- Local speech models are optional explicit installs; do not download model weights during startup.
- Do not store raw audio by default. Clearly disclose any optional remote processing.
- Avoid collecting unnecessary sensitive personal data. Profile information stays local.
- Keep GitHub as code source of truth. Never discard or overwrite a user's uncommitted local work.

## Product quality gates

Every module must have:
- A clear learner outcome and complete usable flow, not just a static screen.
- Server-side validation and persistence where data is involved.
- Automated tests for core behaviour, failure cases, and legacy compatibility.
- Accessible labels, keyboard operation, useful empty/loading/error states, and responsive layout.
- Documentation distinguishing implemented, tested, manually verified, and planned.
- Honest feedback: quote submitted evidence, explain uncertainty, and avoid unsupported proficiency or outcome claims.

## Explicitly not claimed

Until separately implemented and validated, Prepped does not claim expert-level AI tutoring, certified CEFR/IELTS proficiency, accurate pronunciation grading, emotion/personality detection, placement probability, or measured learning outcomes. Optional generative AI must not be a mandatory dependency or fabricate feedback evidence.


---

## Build plan — from foundation to a release candidate

This section turns the product direction into an implementation sequence. It is the active build order; update the status only when code, tests, and acceptance evidence exist.

### Release principle

The learner profile remains a preference record, but its stated goal and focus areas now select a transparent starter route through the Learning Engine and English curriculum. This is route selection, not inferred ability, adaptive difficulty, or a validated assessment.

### Phase A — Stabilise the current foundation

- [x] Confirm profile setup, edit, cancel, save, reload, and persistence in automated Chromium browser tests in CI; target-laptop manual spot check remains.
- [x] Confirm the profile toggle opens/closes, updates `aria-expanded`, and persists edits in automated Chromium; target-laptop manual spot check remains.
- [x] Run the complete pytest suite, Python compilation, and JavaScript syntax checks; the current full suite is [100 passed, 2 skipped, 1 warning](https://github.com/Exploiter69/Prepped/actions/runs/44653868798).
- [ ] Complete the outstanding voice browser acceptance checklist and document microphone, transcription, transcript correction, submission, TTS, and text fallback results.
- [x] Verify CI and a clean-checkout install (GitHub Actions completed successfully on the feature branch; dependency install, compilation, JavaScript syntax, and pytest all passed).
- [x] Keep the existing practice room and saved sessions intact; regression tests cover the text-only journey and additive profile migration.

**Exit gate:** automated Chromium profile and text-practice smoke tests pass; automated checks and CI pass; voice limitations are recorded honestly. The phase remains open until the target-laptop voice/microphone acceptance is performed or explicitly recorded as unavailable.

### Phase B — Learning Engine (implementation added; acceptance in progress)

Build the reusable learning foundation before adding many disconnected screens.

1. **Skill taxonomy:** define stable skill IDs, descriptions, observable learning outcomes, and links between English fluency, grammar, sentence construction, vocabulary, listening, pronunciation, confidence, professional communication, project explanation, and interview skills.
2. **Versioned curriculum manifest:** define tracks, levels, units, lessons, prerequisites, estimated effort, and exercise references in reviewed local JSON. Content must be versioned and validated at startup/test time.
3. **Reusable lesson runner:** support lesson introduction, example, learner exercise, response, feedback, retry, completion, and next-step navigation. Keep scenario/lesson state controlled by application code.
4. **Exercise types:** start with deterministic, testable formats: sentence ordering/construction, grammar-in-context, vocabulary in context, short written/spoken response, listening comprehension using available audio, and explain/describe/compare prompts.
5. **Evidence-based feedback:** explain a correction, show the learner's original text, offer a better example, and state uncertainty. Do not infer proficiency from a single response or fabricate speech/pronunciation measurements.
6. **Progress events:** persist lesson attempts, completion, skill links, timestamps, and feedback references additively in SQLite.
7. **Profile-driven starting route:** map the learner's stated goal and focus areas to a transparent starter path. For example, English fluency plus speaking fluency/grammar/vocabulary should prioritise those units. Show why each recommendation appears and allow the learner to change the route.
8. **Diagnostic — implemented:** a short, low-stakes baseline follows the exercise loop. It stores observable responses and completed tasks, not a certified level.

**Exit gate:** a learner can choose a track, complete a sequence of lessons, receive grounded feedback, retry, resume after restart, and see progress. Profile choices demonstrably affect the suggested starting path. Text mode works without speech models.

### Phase C — English and communication curriculum

Deliver a coherent first track rather than a large empty catalogue.

- English foundations: sentence structure, common grammar patterns, question formation, tense in context, articles/prepositions where useful, and error correction.
- Sentence construction: build, expand, combine, shorten, and clarify sentences; preserve intended meaning.
- Vocabulary: useful words and phrases in context, collocations, definitions, example use, learner-created examples, and review.
- Speaking fluency: structured short responses, retelling, describing, explaining, opinions, and follow-up prompts.
- Listening: short locally available or authored audio, transcript/caption support, comprehension questions, replay, and text alternative.
- Pronunciation: begin with listen-and-repeat/self-review activities. Do not expose phoneme accuracy scores unless a separate validated implementation supports them.
- Confidence: private, repeatable low-pressure practice and visible completion evidence; do not infer emotion or assign a confidence score.

**Exit gate:** each unit has authored content, clear outcomes, exercises, answer handling, feedback, tests, and a complete learner flow. Every audio activity has an accessible text alternative.

### Phase C implementation status — English and communication studio

**Implementation added; automated coverage passes in the current full-suite CI run.** The initial English path is authored in the versioned curriculum and uses the existing Phase B lesson runner. Target-laptop acceptance remains pending.

- The curriculum contains 14 stable skills, one foundation stage, nine units, four tracks, 13 authored lessons plus the separate low-stakes baseline check. Every unit and lesson has explicit learning outcomes; the lesson runner displays the outcomes before exercises. The English foundations track contains 11 sequenced lessons across sentence construction, grammar, vocabulary, listening, speaking, and pronunciation.
- Grammar and sentence work covers complete sentences; expansion, combining, shortening, and clarification; past and future tense in context; articles; prepositions; question formation; and authored error explanations.
- Vocabulary work covers precise words, collocations, phrase meaning, contextual use, and a learner-authored example.
- Speaking work includes structured descriptions, process explanations, project checks, retelling, opinions, reasons, and follow-up responses. Responses can be typed or recorded and transcribed when the configured STT service is available.
- Listening work includes authored spoken updates and short conversations, comprehension choices, replay/stop controls, and an always-available transcript alternative.
- Pronunciation work uses local TTS model phrases, listen-and-repeat prompts, optional spoken recording/transcription, and learner self-review. It does not grade pronunciation, accent, phonemes, or fluency.
- Confidence practice is private and repeatable. No emotion inference or confidence score is generated.
- Profile focus areas for grammar, vocabulary, speaking fluency, pronunciation, confidence, and professional communication now explain which English lessons match. Existing project/interview paths and the original practice room remain available.
- No new paid service, external runtime dependency, database service, or database migration is required for this curriculum expansion. Audio playback uses the configured local TTS service; typed responses remain usable if audio or microphone support is unavailable.

**Remaining Phase C gates:** review the new units in a real browser on the target laptop; verify replay, text alternatives, optional Groq disclosure, transcript editing, text-only fallback, keyboard navigation, and narrow-screen layout; review the lesson content for clarity and usefulness. The content is implemented, but it is not manually accepted until those checks are recorded.

### Phase D — Personal learning memory and revision

**Implementation added; GitHub Actions passes. Target-laptop manual acceptance remains pending.**

- [x] Let learners explicitly save a word, phrase, correction, concept, or useful example manually or from lesson/project-practice feedback.
- [x] Preserve original response/evidence, source title, identifier, and excerpt where available.
- [x] Allow edit, dismiss/restore, delete, suspend/resume, and duplicate resolution.
- [x] Build a transparent local interval scheduler, due queue, rating controls, and review history.
- [x] Keep uncertain automated feedback as an editable suggestion; nothing is saved without learner action.
- [x] Current full-suite GitHub Actions passes: [100 passed, 2 skipped, 1 warning](https://github.com/Exploiter69/Prepped/actions/runs/44653868798); both skips require `espeak-ng`.
- [ ] Complete target-laptop manual acceptance.

**Exit gate:** learners can create/edit/dismiss/suspend/delete review items, complete due reviews, inspect history and scheduling behaviour; tests cover validation, duplicate handling, dates, retries, persistence, and legacy-data compatibility.

### Phase E — Career and interview studios

**Implementation added on `feature/learner-profile`; current full-suite CI is green, and target-laptop acceptance remains pending.**

- [x] Project Explanation Studio: problem/user framing, personal contribution, technical decisions, tests/evidence, limitations, and reflection.
- [x] HR & Behavioural Studio: introduction, teamwork, disagreement/priorities, setbacks, learning, motivation, and preparation.
- [x] Technical Fundamentals Studio: arrays/linked lists, HTTP/API flow, database indexes, and processes/threads.
- [x] Four authored main questions per studio, each followed by a studio-specific follow-up. Guided, standard, and challenging modes select different authored follow-up wording.
- [x] Persisted interview sessions and ordered turns, with versioned content snapshots, resume, history, retry grouping, feedback, and deletion.
- [x] Reuse the existing STT/TTS adapters for optional record/stop transcription, editable transcripts, and spoken prompts. Text remains available.
- [x] Disclose Groq remote-audio processing before microphone permission when that provider is configured. Prepped does not persist raw recordings.
- [x] Provide transparent, evidence-linked reflection without technical correctness grading, overall interview score, recruiter rating, or placement prediction.
- [x] Allow explicit handoff of an answer to the Phase D memory editor; the learner must review and submit before saving.
- [x] Add additive `career_sessions` and `career_turns` tables; preserve existing practice, profile, learning, and memory data.
- [x] Current full-suite GitHub Actions passes: [run 44653868798](https://github.com/Exploiter69/Prepped/actions/runs/44653868798) — 100 passed, 2 skipped, 1 warning; includes all Phase E tests.

- [ ] Complete target-laptop text, voice, persistence, accessibility, and responsive acceptance.

**Exit gate:** all three studios complete through the same reusable state machine; follow-ups, review, retry, resume, delete, and memory handoff work; CI is green; target-device acceptance is recorded. The authored starter question bank is not an exhaustive interview curriculum or a validated hiring assessment.

### Phase F — Progress, portability, and hardening foundations

**Implementation added on `feature/learner-profile`; the current full-suite CI run is green, and target-laptop acceptance remains open.**

- [x] Skill-level progress derived from completed lesson events and linked curriculum skills; no single ability score.
- [x] Local progress overview combines lesson evidence, project practice, interview completions, memory reviews, weekly activity, and recent activity.
- [x] Learner-owned goals for completed lessons, project practice sessions, completed interviews, and memory reviews. Goals can be created, edited, archived/restored, and deleted; progress counts only activity recorded after the goal was created. Recommendation dismissals are persisted and can be restored.
- [x] Explainable next-step recommendations use saved profile preferences, unfinished lesson/practice/interview sessions, due memory reviews, and active goals; learners can dismiss and restore suggestions, with dismissal state persisted locally and included in backups.
- [x] Local JSON export covers profile, sessions/answers, lesson attempts/events, memory items/reviews, career sessions/turns, goals, and dismissed recommendation preferences.
- [x] Restore is explicit full replacement, not merge. It is size/row bounded, validates the backup in a staged database, checks SQLite integrity and foreign keys, and only then replaces the active database.
- [x] Additive `learner_goals` and `recommendation_dismissals` migrations and explicit backup format/database schema versions.
- [x] Local-only Host/Origin guard, restrictive security headers/CSP, no-store API responses, and a database/curriculum readiness endpoint.
- [x] Clean-install and recovery documentation for Linux/Omarchy, plus a release-hardening record.
- [x] CI checks Python compilation, all browser JavaScript syntax, automated API/Chromium tests, and a Python dependency vulnerability audit.
- [ ] Complete target-Omarchy fresh-install and manual end-to-end acceptance for progress, goals, backup/restore, keyboard/screen-reader use, contrast, and responsive layout.
- [ ] Run the optional consent-based usability study only when participants are available; record method, sample size, failures, and limitations. No pilot results are claimed.

**Known boundaries:** backups are unencrypted JSON and contain personal answers; the current 25 MiB / 200,000-record limits and backup format version 1 / database schema version 3 compatibility are deliberate. Restore replaces all current local data. Prepped remains a single-user loopback application, not a public or multi-user deployment.

**Exit gate:** feature implementation, automated suite and CI pass, core journeys are accepted manually, data backup/restore works, known limitations are documented, and no unsupported product claims remain. Manual target-device acceptance is not claimed until recorded.

### Phase G — Release hardening and acceptance (not started)

Phase G begins only after the implemented A–F journeys have been manually accepted on the target Omarchy laptop and the clean-install/recovery checks are recorded. It is a release-readiness phase, not another feature-expansion phase.

- [ ] Close all outstanding A–F checks in [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md), recording environment, result, and any deviations.
- [ ] Complete keyboard-only and screen-reader review, focus order/visibility, labels/status announcements, contrast, and narrow-screen checks across every workspace.
- [ ] Complete fresh-install, upgrade/restart, readiness, backup, and restore rehearsal on the target machine using disposable test data.
- [ ] Review the local-only network boundary, Host/Origin checks, CSP/security headers, dependency audit findings, secret handling, and unencrypted backup warning. This is not a third-party penetration test or a public-hosting approval.
- [ ] Record voice observations (microphone permission, provider disclosure, transcript correction, TTS, failures, text fallback, and any latency/memory observations) without claiming accuracy benchmarks.
- [ ] Fix only issues found by those checks; rerun the complete CI suite on the resulting commit.
- [ ] Keep the student usability pilot optional and separate. If run, use consent, minimal anonymous notes, and report method/sample/limitations.

**Exit gate:** all advertised local core flows are manually accepted; fresh install and recovery are repeatable; automated CI is green; accessibility, privacy, security boundaries, limitations, and evidence are documented. Prepped remains a single-user loopback application unless a separately reviewed architecture and threat model are approved.

### Definition of done for every feature

A feature is not complete because its screen exists. It is done only when:
- The learner outcome and end-to-end flow are defined.
- UI, API, validation, and persistence work together where needed.
- Loading, empty, error, retry, and offline/text-fallback states are handled.
- Automated tests cover normal, invalid, boundary, failure, and legacy-data behaviour.
- Accessibility and responsive behaviour are checked.
- Documentation says whether it is proposed, implemented, automated-tested, or manually accepted.

### Scope and architecture guardrails

Keep the existing Python + FastAPI + plain HTML/CSS/JavaScript + SQLite modular monolith and versioned JSON content. Use additive migrations. No mandatory paid services, hosted dependencies, login, React/Vue/Svelte rewrite, Redis, Kafka, Celery, Kubernetes, microservices, vector database, or second workflow system. Optional AI must be replaceable, explicitly configured, disclosed, and never required for core lessons. Do not store raw audio by default.

### Phase B implementation status — Learning Engine

**Implementation delivered; automated coverage passes in the current full-suite CI run. Target-laptop acceptance remains open.** The first complete vertical slice is in the branch:

- Versioned curriculum/curriculum.v1.json now defines 14 stable skill IDs, one foundation level, nine units, four tracks, 13 authored lessons plus one diagnostic check, outcomes, prerequisites, examples, and authored exercises.
- prepped/learning.py validates skill/track/level/unit/lesson references and supported exercise shapes, exposes a reusable lesson-attempt API, enforces exercise order, presents prerequisites as recommended learning order without blocking lesson access, withholds answer keys from catalogue responses, and produces deterministic feedback for authored choice, vocabulary, listening, and ordering exercises. Open responses are stored for learner self-review; they are not automatically graded.
- Additive SQLite learning_attempts and learning_events tables preserve existing sessions, answers, and the learner profile. Attempts and responses survive application restarts.
- Profile goal and selected focus areas now select a transparent starter route with a reason per recommended lesson. Unsupported focus areas are disclosed rather than silently mapped to unrelated content.
- A new Learning workspace provides skill-map and unit browsing, profile-based recommendations, lesson exercises, local spoken listening and pronunciation playback with text alternatives, optional spoken responses through the configured STT provider, feedback, progress counts, next-lesson navigation, and resume controls. It uses plain HTML/CSS/JavaScript and keeps the existing practice room available.
- API and Chromium acceptance tests cover curriculum validation, answer-key isolation, profile routing, exercise validation/order, prerequisites, completion, persistence, progress events, resume, and legacy-data preservation.

**Remaining Phase B gates:** target-laptop browser check for navigation, all seven exercise formats, listening text alternatives, optional voice controls, next-lesson navigation, reload/resume, and responsive layout; review of lesson wording and learning usefulness. A short, low-stakes starting-point check is now included after the exercise loop was implemented. It stores observable responses and task completion, can be repeated/reviewed, and assigns no proficiency level or overall score. More advanced diagnostic interpretation remains deferred.

The English starter path is expanded under Phase C. Advanced diagnostic interpretation remains deferred; learner-controlled revision is implemented under Phase D; dedicated HR, project, and technical interview studios are implemented under Phase E.


---

## Phase D — Personal learning memory and revision (implementation added; acceptance pending)

**Purpose:** let the learner deliberately retain useful learning from lessons and practise it again later. Memory is user-owned, editable, local, and evidence-linked. No uncertain automated signal becomes a permanent learner trait.

### Delivered in the implementation

- A dedicated local memory API and Learning workspace section.
- Explicit item types: word, phrase, correction, concept, and example.
- Manual item creation plus optional lesson and project-practice feedback suggestions. A suggestion only prefills the editor; the learner must review and submit it before anything is saved.
- Source provenance: source type, lesson/attempt identifier, lesson title, and a short source excerpt are retained when available.
- Edit, suspend/resume, dismiss/restore, and permanent delete controls. Dismissal removes an item from active review without deleting it or its history; permanent deletion cascades to review history.
- Duplicate attempts return the existing item and the UI opens that item for editing instead of silently overwriting it.
- Duplicate detection uses Unicode-normalised, case-folded, whitespace-collapsed text within the same item type. Existing items are not silently overwritten.
- A due-review queue with answer reveal and Again / Hard / Good / Easy ratings.
- A deterministic, transparent interval scheduler implemented locally. It is deliberately a small custom schedule, not FSRS and not claimed to be FSRS-compatible.
- Review history, interval, repetition and lapse counts, next due date, and library statistics.
- Additive SQLite tables and indexes; no existing profile, session, answer, learning attempt, or event data is dropped or rewritten.
- No raw audio, cloud model, paid service, account, hosted database, or new runtime infrastructure is required.

### Scheduler behaviour

- New cards are due immediately.
- Again resets the repetition step and schedules one day later.
- Good schedules 1 day for the first successful review, 3 days for the second, then doubles the prior interval.
- Hard advances the repetition count and multiplies the previous interval by 1.2 (minimum one day).
- Easy schedules 3 days on the first review, then multiplies the prior interval by 2.5 (minimum two days).
- Review timestamps are stored in UTC. The UI displays dates in the browser's local timezone.
- Intervals are capped at 3,650 days (10 years) to keep dates bounded and predictable.
- Suspended cards are excluded from the due queue. Resuming restores their existing schedule.

### Required verification before closing Phase D

- [ ] Full pytest suite and JavaScript syntax checks pass on the final Phase D commit.
- [ ] GitHub Actions is green for that exact commit.
- [ ] Browser test covers create, due queue, reveal, rating, edit, and suspend.
- [ ] API tests cover validation, duplicate detection, edit/source preservation, schedule intervals, review history, suspend/resume, deletion cascade, restart persistence, and legacy-data preservation.
- [ ] Manual target-laptop check confirms the complete memory and review journey, keyboard operation, narrow-screen layout, and persistence.
- [ ] Review wording and scheduler behaviour are documented honestly; no FSRS or learning-gain claims.

**Exit gate:** a learner can intentionally create or capture an item, edit it, resolve duplicates, suspend/resume/delete it, complete a due review, and inspect the next schedule; all data survives restart and tests protect existing Prepped data.
