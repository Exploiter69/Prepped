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
- A baseline diagnostic that records what the learner can currently do; it must not claim validated proficiency.
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
- Recommendations show why they were suggested and let the learner dismiss them.
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
3. Learner baseline diagnostic with transparent, non-certified output.
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

The learner profile is currently a preference record. It does **not** yet power adaptive lessons, recommendations, or an English curriculum. Do not describe the app as a complete personalised learning platform until the learning loop below is implemented end to end.

### Phase A — Stabilise the current foundation

- [x] Confirm profile setup, edit, cancel, save, reload, and persistence in automated Chromium browser tests in CI; target-laptop manual spot check remains.
- [x] Confirm the profile toggle opens/closes, updates `aria-expanded`, and persists edits in automated Chromium; target-laptop manual spot check remains.
- [x] Run the complete pytest suite, Python compilation, and JavaScript syntax checks (GitHub Actions: 41 passed, 2 skipped because espeak-ng is not installed in the runner; one Starlette/httpx deprecation warning).
- [ ] Complete the outstanding voice browser acceptance checklist and document microphone, transcription, transcript correction, submission, TTS, and text fallback results.
- [x] Verify CI and a clean-checkout install (GitHub Actions completed successfully on the feature branch; dependency install, compilation, JavaScript syntax, and pytest all passed).
- [x] Keep the existing practice room and saved sessions intact; regression tests cover the text-only journey and additive profile migration.

**Exit gate:** automated Chromium profile and text-practice smoke tests pass; automated checks and CI pass; voice limitations are recorded honestly. The phase remains open until the target-laptop voice/microphone acceptance is performed or explicitly recorded as unavailable.

### Phase B — Learning Engine (next major product milestone)

Build the reusable learning foundation before adding many disconnected screens.

1. **Skill taxonomy:** define stable skill IDs, descriptions, observable learning outcomes, and links between English fluency, grammar, sentence construction, vocabulary, listening, pronunciation, confidence, professional communication, project explanation, and interview skills.
2. **Versioned curriculum manifest:** define tracks, levels, units, lessons, prerequisites, estimated effort, and exercise references in reviewed local JSON. Content must be versioned and validated at startup/test time.
3. **Reusable lesson runner:** support lesson introduction, example, learner exercise, response, feedback, retry, completion, and next-step navigation. Keep scenario/lesson state controlled by application code.
4. **Exercise types:** start with deterministic, testable formats: sentence ordering/construction, grammar-in-context, vocabulary in context, short written/spoken response, listening comprehension using available audio, and explain/describe/compare prompts.
5. **Evidence-based feedback:** explain a correction, show the learner's original text, offer a better example, and state uncertainty. Do not infer proficiency from a single response or fabricate speech/pronunciation measurements.
6. **Progress events:** persist lesson attempts, completion, skill links, timestamps, and feedback references additively in SQLite.
7. **Profile-driven starting route:** map the learner's stated goal and focus areas to a transparent starter path. For example, English fluency plus speaking fluency/grammar/vocabulary should prioritise those units. Show why each recommendation appears and allow the learner to change the route.
8. **Diagnostic:** add a short, low-stakes baseline only after exercises and feedback are stable. Store observable responses and completed tasks, not a certified level.

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

### Phase D — Personal learning memory and revision

- Let learners explicitly save a word, phrase, correction, or useful example.
- Preserve source context and the learner's original response.
- Allow edit, dismiss, delete, suspend, and duplicate resolution.
- Build a simple transparent local review scheduler only after card quality is demonstrated.
- Integrate due cards into lessons and a dedicated review session.
- Never silently convert uncertain automated feedback into a permanent learner weakness.

**Exit gate:** learners can create/edit/delete review items, complete due reviews, and see scheduling behaviour; tests cover dates, retries, and persistence.

### Phase E — Career and interview studios

- Add project explanation and personal contribution tracks.
- Add HR/behavioural and technical interview scenario packs.
- Add follow-up turns using explicit scenario state and validated transitions.
- Reuse the same session, voice, feedback, and history infrastructure.
- Add role-specific paths only when the content is authored and tested.

**Exit gate:** at least two distinct scenario families run through the same reusable infrastructure without breaking the English learning path.

### Phase F — Progress, portability, and release hardening

- Skill-level progress based on completed activities and observable evidence, not a single opaque score.
- Goals, activity history, review completion, and explainable recommendations.
- Local export, backup, restore, and recovery tests.
- Responsive layout, keyboard and screen-reader checks, contrast, focus, and empty/loading/error states.
- Security review: local binding, input validation, upload limits, secrets, dependency review, and safe data handling.
- Fresh-install test on the target Omarchy laptop and documented supported environment.
- Manual acceptance checklist for all core journeys.
- Small consent-based usability study when feasible; report sample size and limitations. It is not a substitute for engineering tests.

**Exit gate:** reproducible clean install, automated suite and CI pass, core journeys accepted manually, data backup/restore works, known limitations are documented, and no unsupported product claims remain.

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

**Implementation in progress; automated and manual acceptance pending.** The first complete vertical slice is now in the branch:

- Versioned curriculum/curriculum.v1.json defines six stable skill IDs, three goal-based tracks, four lessons, outcomes, prerequisites, examples, and authored exercises.
- prepped/learning.py validates curriculum references and supported exercise shapes, exposes a reusable lesson-attempt API, enforces exercise order and prerequisites, withholds answer keys from catalogue responses, and produces deterministic feedback for choice/order exercises. Open responses are stored for learner self-review; they are not automatically graded.
- Additive SQLite learning_attempts and learning_events tables preserve existing sessions, answers, and the learner profile. Attempts and responses survive application restarts.
- Profile goal and selected focus areas now select a transparent starter route with a reason per recommended lesson. Unsupported focus areas are disclosed rather than silently mapped to unrelated content.
- A new Learning workspace provides curriculum browsing, recommendations, lesson exercises, feedback, progress counts, and resume controls. It uses plain HTML/CSS/JavaScript and keeps the existing practice room available.
- API and browser acceptance tests cover curriculum validation, answer-key isolation, profile routing, exercise validation/order, prerequisites, completion, persistence, progress events, resume, and legacy-data preservation.

**Remaining Phase B gates:** successful latest CI run; target-laptop browser check for navigation, choice/order/reflection exercises, reload/resume, and responsive layout; review of lesson wording and learning usefulness. The baseline diagnostic remains deliberately deferred until exercises and feedback are stable. No proficiency score is produced.

The starter curriculum is deliberately small. Vocabulary, listening, pronunciation activities, HR/technical interview packs, diagnostic assessment, and spaced revision remain later roadmap work.
