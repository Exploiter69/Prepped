# Prepped — Complete Project Roadmap

**Status:** Phases A–H implementation is present. Phase I implementation is present; local pytest reports 145 passed and exact-commit GitHub Actions run [44742961672](https://github.com/Exploiter69/Prepped/actions/runs/44742961672) passed with 143 passed, 2 optional skips, and 1 warning. Target-device acceptance remains pending. Phase J implementation includes curriculum/studio source registers, explicit outcomes and completion conditions, cross-file coverage linting, and per-exercise outcomes, effort estimates, and inherited skill/source context for all 49 exercises. Exact-commit verification and human content/accessibility review remain pending; no learner study has been run. The text MVP is frozen except for material bugs.<br>
**Updated:** 2026-11-20<br>**Future plan:** Phase I acceptance remains open; Phase J human acceptance remains open; Phase K engineering controls and acceptance documentation are implemented, with exact-commit verification and manual failure drills pending; Phase L remains planned.<br>
**Planning basis:** B.Tech semester 3 now; TDP continues through the final year. Dates are decision gates, not promises.<br>
**Companion documents:** [Product Blueprint](PRODUCT_BLUEPRINT.md) · [Current State](CURRENT_STATE.md) · [Voice Setup](VOICE.md) · [ADR-002](ADR-002-LOCAL-VOICE-SLICE.md)

## 1. Destination

Prepped is a **voice-first, personalised AI practice and learning platform** for Indian engineering students. It should help a learner practise realistic placement and professional conversations, speak answers naturally, receive specific feedback tied to what they actually said, retry, and improve over time.

The first job remains concrete: **practise explaining a project to a placement interviewer and handling follow-up questions.** Voice is now part of that first job rather than a distant gate.

The long-term direction may include more scenarios, English fluency practice, technical interview drills, review scheduling, and local personalisation. Those are future work, not claims about the current build.

### Product loop

1. Choose a scenario with a clear goal.
2. Hear or read the interviewer's prompt.
3. Answer by speaking or typing.
4. Review and correct the local transcript.
5. Submit through the same session backend.
6. Receive evidence-linked formative feedback.
7. Retry with the same checklist.
8. Compare attempts and carry useful lessons into later practice.

The first proof is this loop working locally with voice, not an avatar, dashboard, or large architecture diagram.

## 2. Historical baseline snapshot (2026-11-04; superseded by section 18 and CURRENT_STATE.md)

**Status updated 2026-11-04.**

### Implemented and locally tested

- One versioned project-interview scenario with five prompts and a rubric.
- FastAPI, plain HTML/CSS/JavaScript, SQLite, and versioned JSON scenario/rubric.
- Ordered answer capture, empty answers, cancellation, completion, answer limits, retry, attempt comparison, history, and deletion.
- Deterministic, evidence-linked text feedback with no overall score.
- First voice slice:
  - Browser `MediaRecorder` start/stop with a 60-second cap.
  - Optional Groq Whisper (`whisper-large-v3`) or local Vosk speech-to-text.
  - Editable transcript inserted into the existing answer box.
  - Submission through the existing answer endpoint.
  - Local Piper TTS with `espeak-ng` fallback.
  - Play/stop/replay controls.
  - Clear microphone/model/TTS errors and text fallback.
  - No raw audio persistence by Prepped; Groq mode sends audio to the provider only when explicitly configured.
- Automated tests for voice API boundaries, failure handling, text fallback, and a synthetic real-Vosk integration check.
- Uploaded-snapshot audit before the Groq adapter: `29 passed, 1 skipped`. After adding the mocked Groq adapter, the isolated audit suite reports `32 passed, 1 skipped`; this does not represent a live API or laptop acceptance. JavaScript syntax and Python compilation checks pass.

### Not yet evidenced

- Real browser microphone acceptance on the target machine.
- Real Vosk transcription and Piper/espeak-ng playback rechecked on the target machine after the latest hardening changes.
- Speech-recognition accuracy on representative Indian English speech.
- Repeatable voice latency/memory benchmarks.
- Fresh-checkout install, Python compilation, JavaScript syntax checks, and automated tests now pass in GitHub Actions on the feature branch; a fresh-checkout browser smoke test on the target laptop remains outstanding.
- Student usability or voice-specific user validation. No pilot has been run.

### Foundation acceptance update (2026-11-19)

The feature branch now has GitHub Actions coverage for pushes to `feature/**`. The current full-suite result is [run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) — 112 passed, 2 skipped (both require `espeak-ng`, unavailable on the hosted runner), with one Starlette/httpx TestClient deprecation warning. Playwright/Chromium browser tests passed for profile setup/edit/cancel/save/reload and the full text-only practice journey. The [Foundation Acceptance Checklist](ACCEPTANCE_CHECKLIST.md) records the remaining target-laptop and optional voice checks. Do not treat headless CI as microphone or device acceptance.

### Product development and user validation are separate

The student pilot is **not an engineering blocker**. Engineering can build and test the voice slice without waiting for participants.

- **Engineering:** code, automated tests, failure handling, privacy, setup, manual browser acceptance.
- **Future validation:** whether students understand and value the flow, whether transcripts are usable, and whether recognition errors are tolerable. This is documented separately with method, sample size, and limitations.

Do not fabricate pilot results. Do not delay implementation solely because a pilot is not available.

### Frozen text work

The text feedback system is a heuristic baseline, not the product's future. **Do not keep adding phrase heuristics.** Only material bugs should change it. Automated regression tests protect existing behaviour; they should not become the project's main activity.

## 3. Hard constraints

- No mandatory paid APIs, subscriptions, hosted databases, paid hosting, or pay-per-use services.
- The core demo must work locally without an external model account.
- No remote voice processing unless the developer explicitly configures a provider key; the UI/status endpoint discloses remote transcription.
- No raw audio persistence by Prepped; the optional remote provider receives the recording only when explicitly configured.
- GitHub is the source of truth.
- Keep one application and one simple data store until evidence proves a need for more.
- Keep the FastAPI + plain HTML/CSS/JS + SQLite stack. No React/Vue/Svelte migration.
- No Redis, Kafka, Celery, Kubernetes, microservices, vector database, or second workflow engine.
- Keep STT/TTS engines behind replaceable adapters.
- Text mode remains fully functional whenever voice fails.
- No LLM feedback, adaptive intelligence, or pronunciation scoring in this phase.
- Never claim that a planned feature exists; require code, a reproducible demo, and tests.
- Do not present generated feedback as a hiring decision, validated assessment, placement predictor, or speech-accuracy claim.

## 4. Workstreams

| Workstream | Purpose | Status | Expands only when |
|---|---|---|---|
| Product and scenario design | Define the learner task, prompts, and success conditions | Active | User validation identifies a concrete need |
| Voice interaction | Record/stop, optional Groq STT or local Vosk, editable transcript, local TTS | Active | Browser/provider acceptance and usability are understood |
| Core application | Keep the local session/answer flow reliable | Maintained | A material bug or new scenario requires change |
| Feedback and evaluation | Keep the transparent text baseline stable | Frozen except bugs | A separately designed, evidence-led feedback change is approved |
| Privacy and safety | Minimise data, avoid raw audio, provide deletion | Active | Public/multi-user use requires review |
| Personalisation and learning loop | Use practice history to guide future practice | Future | Feedback quality and learner value are demonstrated |
| Second scenario / fluency | Broaden beyond one project-interview scenario | Future | The voice loop is usable and maintainable |
| Academic evidence | Record decisions, tests, limitations, and validation | Continuous | Every phase adds evidence |
| Institutional expansion | Cohorts, faculty views, LMS | Final-year option only | Real stakeholder need and privacy basis exist |

## 5. Phase 0 — Research, truth reset, and scope (done)

**Purpose:** establish a shared, honest project baseline.

Completed:

- Preserved five research reports and verification notes.
- Created product blueprint, roadmap, and research decision matrix.
- Defined the first scenario and rubric.
- Separated prior proposal claims from implemented work.
- Recorded that the old “40% improvement” claim is unsupported.

**Exit gate:** the team can explain who Prepped serves, what the first version does, what it does not do, and how claims will be checked. Met.

## 6. Phase 1 — First local text loop (done; frozen)

**Purpose:** prove the core session/answer/feedback/retry loop.

Delivered:

- Local FastAPI application and browser interface.
- SQLite session/answer persistence.
- Versioned scenario and rubric.
- Evidence-linked heuristic feedback, retry, comparison, history, deletion.
- Automated regression coverage.

**Status:** complete enough to serve as the fallback. Feature development is frozen except material bugs.

## 7. Phase 2 — First voice slice (implemented baseline)

**Purpose:** make the existing scenario genuinely voice-enabled, with a reliable optional free-tier cloud STT path and a local offline fallback.

Delivered:

- Record/stop microphone capture.
- Local Vosk STT fallback; explicit one-time model installation.
- Optional Groq Whisper (`whisper-large-v3`) STT when a server-side `GROQ_API_KEY` is configured.
- In-memory `ffmpeg` decoding; no raw audio persistence.
- Editable transcript before submission through the existing backend.
- Local Piper TTS with `espeak-ng` fallback.
- Play/stop/replay for interviewer prompts.
- Error handling and text fallback.
- Adapter interfaces for STT/TTS replacement; provider selection does not change session APIs.
- Architecture decision and setup/privacy documentation.

**Not delivered in this phase:** streaming, VAD, interruption, always-listening, pronunciation scoring, LLM feedback, personalisation.

**Exit gate:** the scenario can be completed through voice on the target machine, transcript errors can be corrected, prompts can be stopped/replayed, failures fall back to text, and automated tests cover the integration boundaries. The API/adapters are verified; **real browser microphone acceptance is still required** before calling the interaction fully accepted.

## 8. Phase 3 — Voice hardening and target-device acceptance (pre-release acceptance gate)

**Purpose:** turn the first working slice into something reliable enough to build on.

Tasks:

- Run the manual browser acceptance checklist in [VOICE.md](VOICE.md) on the actual laptop.
- Measure warm/cold STT and TTS latency and memory over repeated runs; record the method and environment. Do not call it a benchmark until repeated.
- Test representative Indian English recordings with consent; compare Groq Whisper and Vosk against human reference transcripts without storing raw audio.
- Decide whether Groq Whisper is good enough for the demo and whether a local whisper.cpp adapter is worth evaluating for offline use.
- Improve microphone/recording states only where observed problems justify it.
- Add cancellation/timeout handling if real use reveals a need.
- Keep text fallback and editable transcripts mandatory.
- Add regression tests only for failures found in real use.

**Exit gate:** a written acceptance record covers browser permission, record/stop, transcript editing, submission, TTS play/stop/replay, model failure, and text fallback. Accuracy remains a documented limitation, not a validated claim.

## 9. Phase 4 — Future user validation (not an engineering blocker)

**Purpose:** learn whether the voice-first workflow is understandable and useful.

This phase can run when participants and an appropriate setting are available. It does not block Phase 3 engineering.

Suggested tasks:

- Complete one prompt by voice, correct a transcript error, and submit.
- Play/stop/replay a spoken prompt.
- Deny microphone permission and recover using text.
- Explain what feedback evidence came from their answer.
- Retry and describe one change.

Record only the minimum anonymised observations. Do not collect raw audio, names, or confidential project details. Report sample size, method, failures, and limitations. A positive result is not required.

Also use future validation to check whether students value voice enough to justify further personalisation work. Do not assume it.

## 10. Original Phase 5 proposal — Personalisation and learning loop (core scope delivered under B–F)

**Purpose:** move from one-off practice toward a personalised learning platform without turning uncertain model output into learner traits.

This was a research-era future proposal. Its core learner-controlled memory, review, route selection, and progress scope is now implemented across Phases B–F; future expansion remains evidence-gated.

Candidate steps:

- Turn concrete, evidence-linked weaknesses into learner-controlled review items.
- Link every item to the source answer and explain why it was suggested.
- Let the learner accept, edit, or reject items.
- Deduplicate items and track whether they are used in later attempts.
- Consider a simple local review schedule; FSRS remains a later experiment.
- Consider a local-only model adapter for wording or scenario variation, behind a narrow validated interface, with deterministic fallback.
- Keep assessment off the realtime path.

**Exit gate:** review items are accurate, useful, non-duplicative, and reused. If they are noisy, keep a manual/rules-based list or stop.

## 11. Original Phase 6 proposal — Second scenario and fluency practice (starter scope delivered under C and E)

**Purpose:** prove the scenario/voice layer generalises without becoming a generic platform. The initial communication curriculum and three interview studios now provide the first expansion; broader scenario packs remain future work.

Candidate scenarios:

- Explain a technical concept to a non-technical interviewer.
- Handle a follow-up about a design decision.
- Describe a project setback and what was learned.
- Short professional-communication or English-fluency drills.

Tasks:

- Keep scenario definitions data-driven and validated.
- Reuse the same session, voice, and feedback infrastructure.
- Avoid scenario-specific special cases in the core controller.
- Test dead states, terminal states, and voice fallback for each scenario.

**Exit gate:** two scenarios use the same infrastructure with little special casing, and the second adds demonstrated learner value.

## 12. Phase 7 — Assessment and human calibration (only if needed)

**Purpose:** establish whether any rubric output is consistent enough to present as more than formative guidance.

Tasks:

- Define each criterion in observable language.
- Collect human ratings on anonymised responses with documented instructions.
- Compare deterministic/model-assisted suggestions with human ratings.
- Report disagreements, sample size, and failure types.
- Do not introduce an overall communication score or placement prediction without a defensible basis.

**Exit gate:** a written calibration report exists. If results are weak, keep checklist feedback and make no score claim.

## 13. Phase 8 — Final-year options (not automatic commitments)

Only consider after the voice loop and validation are solid:

- More interview, presentation, teamwork, negotiation, or difficult-conversation scenarios.
- Shadowing and playback-speed controls.
- Pronunciation/prosody feedback if local models and human validation justify it.
- Multilingual practice based on tested need and quality.
- Export of sessions or review items.
- Institution accounts, cohort analytics, SSO, LMS integrations, multi-tenant cloud, mobile packaging, avatars, VR, or marketplace features.

Every new capability needs a problem statement, zero-mandatory-cost plan, acceptance criteria, privacy assessment, and a reason it matters more than improving the current loop.

## 14. Semester-by-semester TDP map

| Semester | Primary objective | Expected evidence / deliverable |
|---|---|---|
| **Semester 3 — reset, text loop, first voice slice** | Build local text loop; add record/stop STT/TTS; document architecture and privacy | Runnable local demo, automated tests, voice setup docs, ADR-002, current-state record |
| **Semester 4 — voice hardening and validation** | Browser acceptance, latency/accuracy observations, failure fixes; run user validation when possible | Acceptance record, measured observations, validation notes with limitations |
| **Semester 5 — personalisation/learning loop** | Evaluate review items and simple local personalisation only if useful | Review-loop prototype, tests, user findings |
| **Semester 6 — second scenario and fluency** | Reuse voice/session infrastructure for a second scenario | Two-scenario demo, scenario schema, learner findings |
| **Semester 7 — assessment and robustness** | Human calibration, privacy/safety, accessibility, failure cases | Calibration report, privacy review, accessibility checklist |
| **Semester 8 — final integration** | Stabilise, document, demonstrate, evaluate | Release candidate, reproducible demo, final report, limitations, future work |

A semester's outcome is evidence, not a feature count. If a gate fails, keep the previous working version and report the finding.

## 15. Testing strategy

### Every change

- Unit/integration tests for affected boundaries and failure paths.
- Regression tests for previously found bugs.
- JavaScript syntax check (`node --check`).
- No secrets, personal recordings, or model weights in Git.

### Voice-specific

- Missing STT package/model.
- Missing `ffmpeg`.
- Empty, silent, oversized, and undecodable audio.
- Denied/unavailable microphone.
- TTS unavailable or failing.
- Transcript edit before submission.
- Text fallback with both engines unavailable.
- No raw audio file created by the transcription path.
- Manual browser microphone check on the target machine before acceptance.

### Before a demo

- Fresh setup from the documented commands.
- Main scenario completes in text and voice modes.
- Feedback evidence matches the answer.
- Retry uses the same rubric.
- Deletion works.
- Missing model or failed voice does not crash the app.
- Keyboard navigation and readable layout work.

### Before user validation

- Clear prototype disclaimer.
- Consent and minimal-data plan.
- No raw audio retention by default.
- Anonymous note-taking process.
- Known limitations documented.

### Before any formal score or institutional data

- Human-rater calibration.
- Privacy and security review.
- Access-control tests.
- Explicit evidence and limitation statement.

## 16. Evidence and claim rules

Every project statement must be one of:

1. **Implemented:** exists in code and can be demonstrated.
2. **Tested:** a repeatable test verifies the behaviour; name the test and its limits.
3. **Observed:** a documented experiment or validation produced results; include method and sample size.
4. **Proposed:** planned but not built.
5. **Hypothesis:** plausible, not established.
6. **Externally reported:** supported by a named source and date.

Do not convert “the model ran” into “speech accuracy is good.” Do not convert “a learner liked it” into “placement outcomes improved.” Do not report a percentage without a denominator, method, and source. Do not describe one-off timings as benchmarks.

## 17. Pre-release sign-off gates (updated 2026-11-20)

1. **Automated verification is green:** [run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) — 112 passed, 2 skipped, 1 warning; compilation, JavaScript syntax, dependency audit, API tests, and Chromium acceptance passed.
2. **Complete manual target-laptop acceptance** for Phases A–F using [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md), including browser, microphone/STT/TTS, keyboard, screen-reader, contrast, responsive, and data-recovery checks.
3. **Complete a clean install and recovery rehearsal** on the target Omarchy laptop using [INSTALL.md](INSTALL.md), with backups tested only against disposable data.
4. **Review limitations and evidence**; do not claim speech accuracy, proficiency, learning gains, placement outcomes, or security certification without validation.
5. **Keep the optional student pilot separate** from engineering. Run it only with consent and available participants; no results are currently claimed.

**Current gate:** Phases A–F are implemented, and Phase G engineering hardening has passed its recorded CI run. Phase G.1 recording lifecycle changes and deferred-permission browser regressions are added and passed in [the final Phase H CI run](https://github.com/Exploiter69/Prepped/actions/runs/44732997261). Manual target-device acceptance remains open and is a release-candidate sign-off gate. See [Phase G Acceptance](PHASE_G_ACCEPTANCE.md).


---

## 18. Updated product completion plan (2026-11-19)

This is the authoritative execution sequence. Earlier sections are the original research/planning model and historical baseline; use this section plus CURRENT_STATE.md for present implementation truth. Phases A–F are implemented. Phase G engineering is implemented and automated CI is green; target-device acceptance remains a release gate. Phase G.1 code and deferred-permission browser regressions are present and green in CI. Phase H implementation and its automated regression suite are also green; later device acceptance remains open.

### Current truth

- The app has the original project-explanation practice scenario, a local session/history flow, formative feedback, a bounded voice record/stop slice, a learner profile, and a reusable Learning Engine.
- The profile goal and focus areas select transparent starter routes through the versioned curriculum; they do not infer ability or adapt difficulty.
- The branch now contains the initial English and communication curriculum, learner-controlled memory and spaced revision, three interview studios, and the Phase F progress/goals/backup/restore workspace. Target-device acceptance for Phases D–F remains outstanding.
- Latest full CI for Phase H and G.1: [run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261) — 134 passed, 2 skipped, 1 warning. The two skips require espeak-ng, unavailable on the hosted runner. Target-device acceptance remains outstanding.
- Do not label this product market-ready or complete.

### Build sequence

| Order | Milestone | Main deliverable | Completion evidence |
|---|---|---|---|
| A | Foundation acceptance | Profile UI/API and current practice/voice flows verified | Browser checklist, pytest, JS/Python checks, CI |
| B | Learning Engine | Skill taxonomy, curriculum manifest, reusable lesson runner, exercise model, progress events | End-to-end lesson path with tests and restart persistence |
| C | English & communication studio | Grammar, sentence construction, vocabulary, fluency, listening and safe pronunciation practice | Complete tested units with feedback and text alternatives |
| D | Personal learning memory | Learner-approved saved words, phrases, corrections and review cards | CRUD, source context, review queue and scheduler tests |
| E | Career & interview studios | Project, HR/behavioural and technical scenarios with follow-ups | Multiple scenario families on shared infrastructure |
| F | Progress & portability | Skill evidence, goals, recommendations, export/backup/restore | Reproducible data recovery and explainable progress |
| G | Release hardening (engineering implemented; device acceptance open) | Security/data edge cases, automated regression, browser/accessibility checks, target-device verification | Phase G acceptance record, green final CI, recovery rehearsal, limitations and release checklist |
| G.1 | Recording lifecycle hardening (implementation, browser regressions, and CI green) | Cancel pending microphone permission, stop streams on every navigation path, abort stale transcription, and protect against late callbacks in Learning and Career | Deferred-permission browser regression tests and green CI |
| H | Adaptive Learning Intelligence (implementation and automated CI green; manual acceptance open) | Evidence-backed skill profile, explainable recommendations, learner-controlled daily/weekly plans, and source-linked analytics | Phase H acceptance record, API/browser regression tests, schema-4 backup compatibility, and green CI |

### Relationship to the original Phase 0–8 planning model

The older Phase 0–8 sections preserve the research-era sequence; they are not a second active build order. Use A–G above for execution:

| Original planning item | Current A–G relationship | Status |
|---|---|---|
| Phase 0–2: research, text loop, first voice slice | Foundation and voice work under A | Implemented baseline |
| Phase 3: voice hardening | Pre-Phase-G target-device acceptance | Manual checks remain |
| Phase 4: student validation | Optional pilot protocol | Not run; not an engineering blocker |
| Phase 5: personalisation and learning loop | B/C learning routes, D memory, F progress/recommendations | Core implementation delivered; manual acceptance remains |
| Phase 6: second scenario and fluency | C communication curriculum and E interview studios | Implemented starter scope; manual acceptance remains |
| Phase 7: assessment and human calibration | Future conditional research | Deferred; no score is approved |
| Phase 8: final-year options | Future options after evidence and stakeholder need | Deferred |

This mapping removes the duplicate numbering: Phase G means release hardening and acceptance only, not the old Phase 7 or a new adaptive-learning feature.

### Milestone B — Learning Engine detailed tasks

1. Define a stable skill taxonomy with skill IDs, learning outcomes, and prerequisites.
2. Define a versioned JSON curriculum format for tracks, units, lessons, exercises, and content references.
3. Validate curriculum files and reject unknown skill IDs, broken prerequisites, missing content, and invalid exercise schemas.
4. Implement a reusable lesson/session runner with explicit states: introduction, example, exercise, response, feedback, retry, completion.
5. Add deterministic exercise types first: sentence ordering/construction, grammar-in-context, vocabulary-in-context, short response, and listening comprehension.
6. Persist attempts, completion, skill links, timestamps, and feedback evidence in SQLite using additive migrations.
7. Connect profile goals and improvement areas to a transparent starter-path selector. Show the reason for each suggested lesson and let learners override it.
8. [Implemented] Add a short baseline diagnostic after the exercises and feedback are stable; it is formative, not a certified language level.
9. Add automated tests for curriculum validation, state transitions, answer limits, feedback grounding, persistence, restart, and compatibility with existing sessions.
10. Keep the existing project-explanation practice route working throughout.

**Milestone B exit criteria:** a learner can open a suggested learning path, complete a lesson, receive grounded feedback, retry, resume after restart, and see completed work. Changing profile goals/focus areas changes the recommended starting path in a deterministic, explainable way.

### Milestone C — English & communication studio

Build a coherent initial English path:
- Grammar in context and common sentence patterns.
- Sentence construction, expansion, combining, clarification, and concise rewriting.
- Vocabulary and useful phrases in context, with learner-authored examples.
- Speaking fluency through short structured prompts: describe, explain, retell, compare, ask, and give opinions.
- Listening comprehension with replay, captions/transcript, and a text alternative.
- Pronunciation practice initially as listen/repeat/self-review. No numerical pronunciation accuracy or phoneme scores without a validated method.
- Confidence-building through private repetition and learner-controlled progress; no emotion inference or automated confidence diagnosis.

Every unit needs an outcome, authored examples, exercises, feedback, tests, and a completion path.

### Milestone D — Personal learning memory

**Implementation added; automated and target-laptop acceptance pending.**

- [x] Save items only through learner action or explicit acceptance.
- [x] Store original response/source evidence and lesson or practice context.
- [x] Support edit, delete, dismiss/restore, suspend/resume, and duplicate resolution.
- [x] Add a transparent local due-date scheduler and dedicated due-review queue.
- [x] Test due-date boundaries, repeated reviews, history, persistence, deletion, and legacy-data preservation.
- [ ] Complete green CI on the final implementation commit and manual target-laptop acceptance.

### Milestone E — Career and interview studios

- Reuse the lesson/scenario runner and existing voice/session APIs.
- Add project explanation and contribution, HR/behavioural, and technical interview tracks.
- Add explicit multi-turn follow-up states and bounded scenario completion.
- Keep feedback tied to submitted answers and rubric versions.
- Add role-specific content only when authored and covered by tests.

### Milestone F — Progress and portability

**Implementation added on `feature/learner-profile`; automated CI is green, while target-device acceptance remains a separate gate.**

- [x] Evidence-based skill coverage linked to completed curriculum lessons, plus activity counts for project practice, interviews, and memory reviews.
- [x] Learner-created goals with create/edit/archive/restore/delete and counts scoped from goal creation time.
- [x] Explainable recommendations from profile preferences, unfinished lessons/practice/interviews, due memory reviews, and active goals, with persistent dismiss/restore controls.
- [x] Full local JSON export and staged, validated full-replacement restore for every learner-data table.
- [x] Backup format/schema versioning, size/record limits, integrity and foreign-key validation, and failure-without-replacement tests.
- [x] Final automated CI pass for the current implementation commit: [run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) — 112 passed, 2 skipped, 1 warning.
- [ ] Complete target-laptop progress and data-recovery acceptance.

### Milestone G — Release hardening and validation

Phase F implemented the initial hardening foundations: local Host/Origin checks, security headers/CSP, readiness checks, dependency audit in CI, and clean-install/recovery/security documentation. Phase G now adds malformed-authority and backup-data edge-case hardening, regression coverage, keyboard/mobile browser acceptance, and a dedicated release record. Remaining release-candidate work includes final CI verification, target-device fresh install and recovery, screen-reader/contrast/voice acceptance, performance observations, and optional consent-based usability validation. No public/multi-user deployment is supported. Do not invent pilot results.

### Release readiness checklist

A release candidate requires all of the following:
- [ ] Every advertised core module has a complete end-to-end learner flow.
- [ ] Profile choices actually affect the learning path and recommendations.
- [ ] English curriculum contains complete, tested learning units.
- [ ] Learner memory and revision work end to end.
- [ ] Interview scenarios reuse the common engine.
- [x] Progress is evidence-based and understandable in the implementation; target-device acceptance remains pending.
- [x] Export/backup/restore is implemented with API round-trip and failure-path tests; target-device acceptance remains pending.
- [ ] Automated tests and CI pass on the final Phase G implementation commit.
- [ ] Fresh-install and target-device checks pass.
- [ ] Accessibility, privacy, security, and failure states are reviewed.
- [ ] Claims and limitations match demonstrated evidence.

## 20. Phase C — English and communication studio implementation update (2026-11-19)

The initial Phase C curriculum has been added to the existing `feature/learner-profile` branch. It extends the Phase B lesson runner rather than introducing a separate learning system.

- **Curriculum size:** 14 stable skills, one foundation stage, nine units, four tracks, 13 authored lessons plus the separate baseline diagnostic. Every unit and lesson has explicit learning outcomes, displayed by the lesson runner. The English foundations track contains 11 sequenced lessons.
- **Grammar:** sentence patterns, past/future tense in context, articles, prepositions, question formation, and answer explanations.
- **Sentence construction:** build, expand, combine, shorten, and clarify while preserving intended meaning.
- **Vocabulary:** contextual word choice, collocations, phrase meaning, examples, and learner-authored sentences.
- **Speaking:** describe, explain a process or feature, retell, give opinions and reasons, and respond to follow-up prompts. Typed answers remain available when speech input is unavailable.
- **Listening:** authored spoken updates and conversations with replay, comprehension checks, and transcript alternatives.
- **Pronunciation:** local TTS model phrases, listen/repeat, optional recording/transcription, and learner self-review. No automated pronunciation, accent, phoneme, or fluency score is produced.
- **Confidence:** private repeatable activities without emotion inference or a confidence score.
- **Personalisation:** profile goals and focus areas now explain matching English lessons; no ability or proficiency is inferred.
- **Compatibility:** existing project-communication tracks and the original practice room remain in place. No new database service, paid API requirement, or database migration was introduced.

Automated API and Chromium coverage for curriculum inventory, profile focus routing, question/grammar/vocabulary handling, listening alternatives, and pronunciation self-review passes in [the current full-suite CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341). Target-laptop browser, audio, microphone/STT disclosure, transcript-editing, keyboard, and responsive acceptance remain manual gates.

The Phase C implementation does not claim certified English proficiency, pronunciation accuracy, improved learning outcomes, or hiring/placement probability. Open speaking responses are retained as learner work and are not automatically graded.

A student usability pilot is useful evidence but does not block engineering. A release must not claim certified English proficiency, accurate pronunciation scoring, placement probability, or measured learning gains without separate validation.

## 19. Phase B — Learning Engine implementation update (2026-11-19)

The first reusable learning-engine slice has been committed to feature/learner-profile. It adds a versioned local curriculum manifest, 14 stable skill definitions, one foundation level, nine units, four tracks, 13 authored lessons plus one diagnostic check, explicit outcomes and prerequisites, and seven exercise formats: choice, ordering, vocabulary, listening, short response, reflection, and pronunciation.

The FastAPI learning router validates the manifest and provides catalogue, recommendations, attempt start/read/response, and progress endpoints. The lesson runner enforces exercise order and prerequisite completion, keeps answer keys out of public catalogue/active exercise payloads, persists responses and feedback, and allows in-progress attempts to resume after restart. Additive SQLite attempt/event tables preserve all existing practice and profile records.

Profile goal/focus preferences select a transparent route with per-lesson reasons. The browser workspace supports skill and unit browsing, recommended lessons, all seven exercise formats, local TTS listening and pronunciation playback with text alternatives, optional STT responses, next-lesson navigation, response feedback, progress counts, and resuming unfinished lessons. Choice and ordering items have deterministic answer feedback; open responses are saved for self-review without automatic grading or proficiency claims.

Automated API and Chromium tests have been added. This implementation is included in the green [full-suite CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341). Target-laptop browser acceptance remains a separate open gate. A low-stakes starting-point check is included. It records sentence, ordering, listening, and project-response tasks; attempts can be repeated and reviewed. It assigns no proficiency level or overall score. More advanced diagnostic interpretation remains future work. Dedicated HR, project, and technical interview studios are now implemented under Phase E. Learner-controlled revision is implemented under Phase D; its automated and target-laptop acceptance gates remain open.


---

## Phase D implementation update — personal learning memory and revision (2026-11-19)

Phase D has been implemented on `feature/learner-profile`. Automated CI passes; target-laptop manual acceptance remains before the phase can be closed.

- Learners can create words, phrases, corrections, concepts, and examples manually.
- Lesson and project-practice feedback include a **Save a learning note** action. It opens an editable prefilled form and never saves automatically.
- Saved items retain source lesson or project-practice metadata, original response/evidence, and a short excerpt where available.
- Items can be edited, suspended, resumed, dismissed/restored, or permanently deleted. Dismissal preserves the card and its history but removes it from active review; delete cascades to review history.
- Duplicate attempts identify the existing item and open it for editing rather than overwriting it.
- Duplicate detection normalises Unicode, case, and whitespace within each item type and returns the existing item identifier instead of overwriting it.
- The due queue supports answer reveal and Again / Hard / Good / Easy ratings.
- The local scheduler is a small deterministic interval schedule. It is not FSRS. New items are due immediately; rating outcomes and interval rules are described in the Product Roadmap.
- Review history and per-item schedule state persist in additive SQLite tables. Existing practice, profile, and learning data are preserved.
- The implementation uses the existing FastAPI + SQLite + plain JavaScript stack and introduces no paid service or infrastructure dependency.

**Verification:** GitHub Actions passes on the final Phase D implementation (79 passed, 2 skipped; both require `espeak-ng`). The remaining gate is manual target-laptop keyboard, responsive-layout, persistence, and end-to-end acceptance. Do not mark Phase D closed until that device acceptance is recorded.


---

## Phase E — Career & Interview Studios implementation update (2026-11-19)

The Career workspace is implemented on `feature/learner-profile`. The current full-suite GitHub Actions run [44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341) passes 100 tests with 2 optional `espeak-ng` skips and 1 warning. Target-laptop acceptance remains outstanding.

- Three versioned studios: project explanation, HR/behavioural interviews, and technical fundamentals.
- Four authored main questions per studio, each followed by an authored follow-up. Guided, standard, and challenging modes choose different follow-up wording.
- FastAPI interview session APIs with ordered turns, persisted session snapshots, resume, recent history, retry grouping, feedback, and deletion.
- Additive `career_sessions` and `career_turns` tables; existing practice sessions, learner profile, curriculum attempts/events, and Phase D memory are preserved.
- Browser workspace supports typed answers, record/stop transcription through the existing voice adapter, editable transcripts, and spoken prompts through existing local TTS. Text remains available when voice is unavailable.
- Groq transcription disclosure is shown before requesting microphone permission when the configured STT engine is Groq. Raw recordings are not stored by Prepped.
- Question-by-question reflection uses transparent text signals and exact answer evidence. It does not claim technical correctness, expert recruiter evaluation, interview success, or placement probability.
- Learners can explicitly send an answer into the Phase D memory editor with its question/session source context. The learner must review and submit the item; no automatic memory writes occur.

The automated suite covers the API state machine, all studio content, difficulty-specific follow-ups, persistence, retry, deletion cascade, legacy practice preservation, browser completion/resume/review, and the memory handoff. The full current implementation suite passes in [CI run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341); target-laptop acceptance remains open before Phase E can be called fully accepted.


---

## Phase F — Progress, portability, and hardening foundations (2026-11-20)

Phase F is implemented on `feature/learner-profile`. The complete current CI workflow passes on [run 44721637341](https://github.com/Exploiter69/Prepped/actions/runs/44721637341): 112 passed, 2 skipped, 1 warning. The workflow completed Python compilation, all six JavaScript syntax checks, dependency installation, `pip-audit`, Chromium installation, API tests, and browser acceptance.

Delivered: evidence-linked skill/activity progress; learner-owned goals; explainable recommendations with persistent dismiss/restore; JSON export and staged full-replacement restore covering every learner-data table; schema/format version checks; local Host/Origin restrictions; security headers/CSP; readiness checks; and install/recovery/security documentation.

**Still open:** target-laptop acceptance for all A–F learner journeys, fresh-install/recovery rehearsal, voice hardware/provider checks, keyboard/screen-reader/contrast/responsive review, and any fixes arising from those checks. The two CI skips require `espeak-ng` and are not counted as passes. The student pilot remains optional future validation, not a prerequisite to engineering.

**Phase G engineering is implemented; target-device acceptance remains open.** Target-device acceptance is still required for release-candidate sign-off; it does not block code-level hardening and automated regression work.


---

## Phase G.1 — Recording lifecycle and privacy hardening (implementation, browser regressions, and CI green)

Before beginning adaptive learning work, verify the microphone lifecycle fix across Learning and Career:

- Invalidate a pending `getUserMedia()` request when the learner navigates away, exits a lesson/interview, changes the active workspace, or unloads the page.
- If a permission request resolves after cancellation, immediately stop every returned media track and never construct/start a `MediaRecorder`.
- Stop active recording and release tracks on every workspace transition, including direct Learning ↔ Career ↔ Progress navigation.
- Abort an in-flight transcription request on cancellation/navigation; ignore late success/error/finally callbacks so they cannot overwrite another screen or insert a stale transcript.
- Preserve intentional Stop behaviour: a learner-requested stop may finish transcription while remaining in the same active exercise/interview.
- Add browser regressions using deferred microphone permission promises for both Learning and Career, plus stale-transcription cancellation where practical.

**Exit gate:** automated browser tests prove that late permission grants do not start recording, all returned tracks are stopped, navigation cancels capture/transcription, and ordinary record/stop/transcript editing still works. This engineering prerequisite does not replace later manual device acceptance.

## Phase H — Adaptive Learning Intelligence (implementation and automated CI green; manual acceptance open)

**Purpose:** turn the existing profile, curriculum, lesson attempts, memory reviews, career sessions, and progress events into a coherent, explainable learning loop. Phase H must reuse the current FastAPI + SQLite modular monolith and existing evidence; it must not introduce a second learner-state system or opaque ability score.

### H1. Evidence-backed learner skill profile

- Define skill-state records from existing curriculum skill IDs and observable evidence already captured by lessons, exercises, project practice, Career sessions, and learner-approved memory reviews.
- Separate evidence of activity from evidence of demonstrated performance. Do not treat lesson completion, one answer, self-reported confidence, or heuristic Career feedback as proof of mastery.
- Track evidence source, timestamp/freshness, quantity, and confidence/coverage limitations; retain links to the underlying attempts and responses.
- Explain why a skill is marked as practised, developing, needs review, or has insufficient evidence. Use conservative deterministic rules; do not claim certified proficiency.

### H2. Deterministic adaptive learning engine

- Recommend the next lesson or exercise using prerequisite relationships, recent evidence, repeated observable errors, learner goals, and due revision items.
- Adapt practice sequence and challenge only where authored content supports it. Do not fabricate exercises or infer traits from voice, accent, emotion, or personality.
- Explain every recommendation with its evidence and let learners dismiss or override it.
- Keep the current profile-based route as a stable fallback when evidence is sparse or ambiguous.

### H3. Daily and weekly learning plan

- Combine due memory reviews, a focused weak/under-practised skill, the next suitable lesson, and optional interview practice into a realistic plan.
- Respect learner-set goals and available time without requiring notifications, background workers, or external services.
- Let learners complete, skip, reorder, and regenerate plan items; explain why each item appears.

### H4. Learner analytics and history

- Show skill-by-skill evidence timelines, practice consistency, revision retention signals, recurring corrections, and progress over time.
- Distinguish completed activity, correct closed-exercise responses, open self-review responses, and heuristic feedback. Do not combine them into a misleading score.
- Provide source links and time windows; state when there is too little evidence to draw a conclusion.

### Phase H guardrails and exit gate

- ₹0 mandatory cost; no required LLM/API, hosted database, queue, Redis, Celery, vector store, or new service.
- Reuse current tables and APIs first; add only small, additive SQLite migrations when a persisted concept cannot be derived safely.
- Deterministic and inspectable first; no opaque mastery score, CEFR certification, learning-gain claim, placement prediction, or automated confidence/personality inference.
- Tests must cover sparse data, conflicting/stale evidence, repeated attempts, prerequisites, learner overrides, backup/restore compatibility, and legacy records.
- Exit only when a learner can understand their evidence, receive a defensible next-step plan, override it, and see why the system changed its recommendation. Manual user validation remains separate from engineering completion.

**Status:** Phase H implementation and Phase G.1 recording lifecycle regressions pass the full automated suite: [run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261) — 134 passed, 2 optional espeak-ng skips, 1 Starlette deprecation warning. Manual target-device and learner acceptance remain separate later gates. See [Phase H Acceptance](PHASE_H_ACCEPTANCE.md).


**Phase H implementation note (2026-11-20):** The evidence model, deterministic recommendations, daily/weekly plans, Progress UI, additive schema-4 plan tables, backup migration from schema 3, and API/browser regression tests have been added. No difficulty adaptation is claimed because the authored curriculum has no difficulty metadata. Do not mark H accepted until the exact final commit has green CI and the later Omarchy acceptance is recorded.

**Final automated evidence (2026-11-20):** [GitHub Actions run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261), commit ba5d4091c3679afe6b261852ca87f2940ba40877 — 134 passed, 2 skipped, 1 warning. Python compilation, seven JavaScript syntax checks, dependency consistency, pip-audit, Chromium setup, API tests, and browser acceptance passed. Manual Omarchy/device acceptance remains open.

---

## 19. Future execution roadmap — Phases I–L (planned; not started)

**Planning status (2026-11-20):** Phases I–L are now defined as the next proposed execution sequence after Phase H. This section is a plan, not evidence that any of these capabilities exist. Start each phase only after reviewing the preceding phase's exit evidence and confirming the scope. Do not mark a phase complete from documentation, a mock-up, or passing isolated unit tests alone.

### Roadmap intent and ordering

The next four phases move Prepped from a feature-rich local prototype toward a trustworthy, coherent, locally usable release candidate:

- **I — Voice Intelligence & Coaching:** make the existing voice and scenario flows feel like a coherent turn-based practice experience, with contextual coaching grounded in the learner's actual responses.
- **J — Curriculum Quality & Learning Validation:** improve the authored learning experience and establish what learners can and cannot reliably achieve with it through content review and carefully bounded evaluation.
- **K — Security, Privacy & Reliability:** review and harden the application and its data lifecycle before calling it release-candidate safe.
- **L — Release Candidate, Packaging & Operations:** make installation, use, recovery, maintenance, and demonstration reproducible, with a release decision based on evidence.

The sequence is deliberate. Better coaching should use stable voice/session behaviour (I); curriculum quality and evaluation should build on coherent practice (J); security and reliability review should consider the actual product surface after those changes (K); packaging and release operations should be completed against the hardened product (L). Critical security or privacy defects discovered earlier must be fixed immediately rather than deferred to K.

### Non-negotiable constraints for every phase

- Maintain the ₹0 mandatory development and operating-cost target. No required paid API, model endpoint, subscription, hosted database, paid hosting, or pay-per-use service.
- Preserve the FastAPI + SQLite + plain HTML/CSS/JavaScript modular monolith, versioned local JSON content, and one application/data store.
- Do not introduce React/Vue/Svelte, Redis, Kafka, Celery, Kubernetes, microservices, a vector database, or a second workflow engine.
- Prefer deterministic, inspectable local behaviour. Optional local models may be evaluated only when their installation, hardware cost, licence, resource use, fallback, and privacy implications are documented.
- Remote processing must remain explicitly optional, disclosed before capture/submission, and never required for the core learner journey.
- No raw audio persistence by default. Keep transcripts editable and provide text-only alternatives for all essential flows.
- Preserve existing learner data and compatibility. Use additive SQLite migrations only when necessary; test old backups and existing records before changing formats.
- Do not infer emotion, personality, accent quality, confidence, hiring suitability, or proficiency from voice. Do not claim CEFR/IELTS certification, placement prediction, learning gains, or validated assessment without a separate defensible study.
- Keep GitHub as the source of truth. Never discard uncommitted local work or use destructive resets to make a phase fit.
- Every phase must update CURRENT_STATE.md and its own acceptance record only when evidence exists. Clearly distinguish implemented, automated-tested, manually accepted, observed, and proposed work.

---

### Phase I — Voice Intelligence & Contextual Coaching

**Status (2026-11-20):** Implementation is present. Local pytest on commit `c4200e5fc06ccfcd06c9b49fadc6cc8d6ac9afdc` reports 145 passed, 0 failed, and one Starlette/httpx deprecation warning. Exact-commit GitHub Actions [run 44742961672](https://github.com/Exploiter69/Prepped/actions/runs/44742961672) passed: 143 passed, 2 optional voice skips, 1 warning. Manual target-device acceptance remains pending. The user authorised Phase J implementation to begin while Phase I manual checks are deferred; Phase I remains open. See [Phase I Acceptance](PHASE_I_ACCEPTANCE.md).

**Purpose:** turn the current record/transcribe/playback and scenario flows into a dependable, context-aware, turn-based voice practice experience. The goal is not a general-purpose always-listening chatbot. It is to help a learner practise a defined communication task, understand a response, and make a useful next attempt.

**I0. Baseline and interaction contract**
1. Audit the existing Learning, Project Practice, and Career voice paths, STT/TTS adapters, browser recording lifecycle, session state, and Phase G.1 regressions before changing code.
2. Define one shared interaction contract for prompt playback, recording, stop, transcription, transcript editing, submission, feedback, retry, cancellation, navigation, and recovery.
3. Document which workspace owns each active recording/transcription operation and what happens on navigation, page unload, timeout, permission denial, duplicate clicks, and late provider responses.
4. Preserve the existing text journey as a first-class path, not merely an emergency error screen.
5. Record a baseline on the target laptop: supported browser, microphone permission behaviour, configured STT/TTS engines, resource use, and reproducible failure cases. Do not invent latency or accuracy targets before measuring the hardware and current behaviour.

**I1. Voice pipeline reliability and usability**
1. Consolidate duplicated browser-side recording/transcription lifecycle logic only where the audit proves it can be shared safely; do not perform a broad frontend rewrite.
2. Make recording states explicit and accessible: idle, requesting permission, recording, stopping, transcribing, transcript ready, failed, and cancelled.
3. Ensure stop, cancel, retry, navigation, and timeout have distinct semantics. A normal learner-initiated stop must still complete transcription; cancellation must prevent stale results from changing the current screen.
4. Validate audio type, duration, size, empty/silent payloads, decoder errors, unsupported browsers, missing local models, missing binaries, provider timeouts, and malformed provider responses.
5. Keep microphone permission requests user-initiated. Never record in the background or leave a stream active after the owning activity ends.
6. Make transcript correction easy before submission; preserve the learner's edited text as the submitted answer and make clear when a transcript is machine-generated.
7. Improve TTS prompt playback controls (play, stop, replay, unavailable state) and ensure the prompt text is always visible or otherwise accessible.
8. Make STT/TTS provider selection and status truthful. Optional Groq use must be disclosed before audio capture; local mode must not silently fall back to a remote provider.
9. Add bounded timeouts, cancellation, and clear recovery messages without introducing background workers or another job system.

**I2. Contextual, bounded coaching**
1. Define a small scenario state model for the existing Project Explanation, HR/Behavioural, and Technical Interview studios. The model must track the current authored prompt, previous learner response, follow-up eligibility, and terminal/retry state.
2. Add contextual follow-up selection using authored follow-up banks and transparent deterministic rules first. A follow-up must relate to the current question or a clearly identified evidence gap; do not invent technical facts.
3. Allow the learner to request a repeat, clarification, simpler wording, or another attempt without losing the current session.
4. Provide response coaching tied to the actual submitted answer: identify observable structure or completeness signals, quote the relevant evidence, explain uncertainty, and suggest one actionable improvement.
5. Keep formative reflection distinct from correctness checking. Technical answers must not be labelled correct unless a reviewed answer key or an explicit deterministic check supports that judgement.
6. Do not add a composite score, personality/emotion inference, accent judgement, confidence diagnosis, hiring score, or placement prediction.
7. If an optional local language model is later considered, first write a separate decision record covering licence, model size, RAM/CPU suitability on the target laptop, offline operation, prompt/data boundaries, hallucination tests, deterministic fallback, and zero-cost maintenance. It must not become a mandatory runtime dependency or be allowed to fabricate evidence.

**I3. Connect coaching to the existing learning loop**
1. Let the learner explicitly save a useful correction, phrase, concept, or next-practice action to the existing Memory editor; never save automatically.
2. Where a source-linked skill is already defined, associate practice evidence with that existing skill ID. Do not create duplicate learner profiles or a second evidence store.
3. Allow an accepted coaching action to become a learner-controlled item in an existing daily/weekly plan, with a visible source and reason.
4. After retry, show the original and revised answer side by side and identify the learner-visible change without claiming measured improvement from one attempt.
5. Preserve session history, versioned scenario snapshots, deletion behaviour, backup/restore compatibility, and the existing Phase H evidence semantics.

**I4. Tests, documentation, and acceptance**
- API tests: state transitions, follow-up eligibility, session resume, duplicate submission, invalid input, timeout, provider failure, and data persistence.
- Browser tests: full voice and text journeys in Learning and each Career studio; permission denial; late permission grant; cancellation; stale response; transcript edit; prompt replay; navigation; keyboard and narrow-screen use.
- Adapter tests: local STT/TTS unavailable, optional provider unavailable, malformed response, timeout, and no silent remote fallback.
- Privacy tests/inspection: no raw audio written to disk or database by the default path; remote disclosure appears before capture when applicable.
- Manual target-device acceptance on the actual laptop with the documented local engines and browser. Record hardware, browser, model versions, observed failures, and limitations.
- Add a Phase I acceptance document with exact commands, test evidence, manual checklist, and known limitations.

**Phase I deliverables**
- Shared, documented voice interaction contract and state model.
- More reliable accessible voice controls and recovery behaviour.
- Contextual authored follow-ups and evidence-grounded coaching.
- Explicit learner-controlled handoff into Memory and adaptive plans.
- API/browser/adapter regressions and a target-device acceptance record.

**Phase I exit gate:** a learner can complete at least one full scenario in text mode and voice mode, correct a transcript, receive response-specific coaching, answer a relevant follow-up, retry, resume, and inspect or explicitly save a useful learning item. Cancellation and navigation cannot leak microphone streams or apply stale results. Automated tests are green and target-device limitations are recorded. No unvalidated score or speech-accuracy claim is introduced.

---

### Phase J — Curriculum Quality, Content Expansion & Learning Validation

**Status (2026-11-20):** Implementation started after the initial curriculum audit. See [Phase J Acceptance](PHASE_J_ACCEPTANCE.md) and [Content Review Log](CONTENT_REVIEW_LOG.md). Human subject-matter review and learner evaluation remain pending.

**Purpose:** make the learning content coherent, accurate, appropriately sequenced, and useful, then gather bounded evidence about usability and learning experience. This phase is about instructional quality and evaluation—not adding a large number of screens or claiming that the app improves placement outcomes.

**J0. Curriculum audit and learning outcomes**
1. Inventory every existing track, skill, unit, lesson, exercise, prompt, answer key, example, and follow-up in the versioned curriculum.
2. Check each item for a clear learner, context, prerequisite, observable outcome, estimated effort, and completion condition.
3. Identify duplicated, contradictory, under-scaffolded, overly difficult, culturally narrow, or unsupported content.
4. Map the current English, professional communication, project explanation, HR/behavioural, and technical fundamentals content to a coherent progression.
5. Distinguish authored content from generated or illustrative examples; no model-generated content is treated as reviewed curriculum by default.
6. Establish a content review checklist and a versioning policy. Curriculum changes must validate at startup and in CI.

**J1. Instructional design and practice quality**
1. Improve lesson structure where needed: explain, demonstrate, practise with guidance, retrieve from memory, apply in a new context, reflect, and revisit.
2. Add worked examples and progressively less-supported practice only where the content author can justify the progression.
3. Expand retrieval practice, spaced review, mixed practice, and scenario transfer using existing lesson, Memory, and plan infrastructure.
4. Ensure listening content has transcripts/captions and every essential audio activity has a usable text alternative.
5. Ensure speaking activities include clear task instructions, reasonable response boundaries, examples where helpful, and a private retry path.
6. Add realistic Indian college and early-career contexts without assuming a single region, language, institution, gender, or socioeconomic background.
7. Expand content by demonstrated learner need, not catalogue size. Prioritise depth and completeness of existing tracks before adding new tracks.
8. Add curriculum linting for missing outcomes, invalid references, broken prerequisites, duplicate IDs, unreviewed answer keys, missing text alternatives, and unsupported exercise types.

**J2. Technical and domain correctness review**
1. Review grammar explanations, vocabulary usage, sample responses, interview prompts, and CS fundamentals against credible references or qualified human review.
2. Maintain source notes for claims that depend on external facts; do not embed uncited or outdated technical claims as authoritative teaching material.
3. Separate questions with objectively checkable answers from open-ended communication prompts.
4. Define acceptable answer variants and edge cases for deterministic exercises; ambiguous items must use self-review rather than false right/wrong feedback.
5. Record reviewer, review date, content version, changes, and unresolved disagreements where human review is available.
6. Do not imply that a single reviewer or a small sample certifies the entire curriculum.

**J3. Accessibility, inclusion, and learner control**
1. Review keyboard navigation, focus order, semantic structure, screen-reader labels/status announcements, contrast, zoom, and responsive layouts across all learner journeys.
2. Keep captions/transcripts, playback controls, adjustable practice pace, and text alternatives available.
3. Make plans, recommendations, reminders (if any), and review schedules controllable and dismissible; avoid guilt-inducing streaks or punitive language.
4. Provide clear explanations of what is stored, where it is stored, how to export it, and how to delete it.
5. Avoid collecting demographic or sensitive information unless a clearly justified, consented research protocol requires it; do not use such data for automated profiling.

**J4. Learner validation protocol**
1. Write a small, consent-based usability protocol before recruiting participants: research question, tasks, inclusion criteria, sample-size rationale, risks, data collected, retention, withdrawal, and reporting plan.
2. Start with usability questions: can learners find a task, understand the prompt, complete it, correct a transcript, interpret feedback, and recover from a voice failure?
3. If evaluating learning, define a narrow skill-specific task and an appropriate pre/post or delayed-recall method before collecting results. Do not use placement, hiring, or broad English-proficiency outcomes as proxies.
4. Use only data necessary for the stated question. Prefer anonymous task observations and learner feedback; do not collect raw voice recordings by default.
5. Report the actual participant count, recruitment context, task completion, observed issues, missing data, limitations, and negative or mixed findings.
6. Do not describe a convenience sample as representative. Do not claim causal learning gains from an uncontrolled short pilot.
7. Keep participation optional and separate from access to the software. Provide a clear withdrawal/deletion path for research notes where applicable.

**J5. Tests and acceptance**
- Curriculum schema and lint tests cover every authored content object and all references.
- Exercise tests cover correct answers, acceptable variants, ambiguous answers, empty input, retry, and text alternatives.
- Browser tests cover complete lesson and scenario journeys, accessibility smoke checks, and responsive behaviour.
- Content review log records what was reviewed and what remains unreviewed.
- If a learner pilot is run, its protocol and results are documented separately from engineering test results.

**Phase J deliverables**
- Audited and versioned curriculum with a documented quality checklist.
- Improved lesson sequencing, worked examples, retrieval/revision, and scenario transfer where justified.
- Content source/review records and automated curriculum linting.
- Accessibility and inclusive-language review.
- Optional consent-based usability/learning study protocol and honest findings (if participants are available).

**Phase J exit gate:** all content included in the release candidate has valid references, explicit outcomes, reviewed deterministic answer keys, and accessible alternatives. Core learning journeys pass automated tests and accessibility checks. Any learner evaluation has documented consent, method, sample, results, and limitations; if no participants are available, the protocol is ready and the absence of results is stated plainly. No learning-gain or placement claim is required to pass.

---

### Phase K — Security, Privacy, Data Protection & Reliability

**Purpose:** establish a defensible security and privacy baseline for the actual intended distribution model. The first target is a reliable local single-user release. Public or multi-user deployment is not silently included.

**K0. Threat model and scope**
1. Write a lightweight threat model covering local browser access, loopback networking, Host/Origin handling, malicious websites, untrusted imports, filesystem permissions, local users, backups, optional remote STT, dependency supply chain, and accidental secret exposure.
2. Define assets, trust boundaries, attackers, impact, mitigations, residual risk, and out-of-scope threats.
3. Confirm the intended release model: local single-user application. Treat LAN, reverse-proxy, tunnel, public internet, shared computer, and multi-user modes as unsupported unless separately designed and approved.
4. Review every API route and state-changing operation for authentication assumptions, validation, CSRF/origin handling, resource limits, and safe error responses.
5. Document the limits of local security: a local application cannot protect data from a fully compromised host account or administrator.

**K1. Application and API security**
1. Review request parsing, content types, body limits, path/query parameters, SQL access, file handling, template/DOM rendering, and browser storage for injection and abuse paths.
2. Verify parameterised SQL, strict allowlists, schema validation, safe serialization, and output escaping.
3. Recheck loopback binding, Host validation, Origin policy, CORS posture, CSP, frame restrictions, MIME sniffing protection, referrer policy, permissions policy, and cache directives.
4. Test malformed, oversized, deeply nested, truncated, duplicate, and adversarial backup/import payloads; invalid input must fail closed without corrupting live data.
5. Ensure errors do not expose stack traces, filesystem paths, secrets, raw prompts containing private data, or database contents.
6. Add rate/size/time bounds appropriate to a local app without introducing a new infrastructure service.
7. Audit microphone permissions and remote-provider boundaries. Only the explicitly selected provider may receive audio, and only after the learner is informed.

**K2. Privacy and data lifecycle**
1. Create a data inventory for profile fields, answers, transcripts, learning evidence, Memory items, Career sessions, goals, plans, backups, logs, and optional provider requests.
2. Document purpose, storage location, retention, export, deletion, and any external recipient for each data category.
3. Minimise collected fields and avoid collecting sensitive demographic data or raw recordings without a separate justified consent process.
4. Review permanent deletion and cascading behaviour across sessions, answers, memory, reviews, plans, analytics, and backups.
5. Decide whether local backup encryption is feasible with standard libraries and a learner-held secret without making recovery fragile. If not implemented, clearly label backups as sensitive and unencrypted.
6. Review permissions and file locations for SQLite DBs, exported backups, logs, configuration, and model caches. Never commit keys, transcripts, recordings, or personal backups.
7. Document optional Groq data handling based on current provider terms and configuration; do not make unsupported claims about provider retention.
8. Provide a privacy notice in the app and a concise data-management/recovery guide.

**K3. Dependency and supply-chain hygiene**
1. Review direct and transitive dependencies, supported Python versions, licence compatibility, known vulnerabilities, and maintenance status.
2. Keep a reproducible dependency lock or documented constraints consistent with the repository's existing packaging approach; do not add a second package manager.
3. Run dependency audit in CI and document exceptions with reason, owner, and review date.
4. Pin or constrain browser/test tooling as appropriate; keep model weights outside Git and verify download sources/checksums when documented.
5. Review the licence and redistribution requirements for any bundled content, audio, fonts, models, and third-party assets.

**K4. Reliability and recovery**
1. Exercise SQLite integrity checks, foreign-key checks, migration from every supported schema, backup export, restore, and rollback-on-invalid-import.
2. Test process termination during writes, disk full/permission errors, corrupt database handling, missing model files, unavailable audio devices, and provider timeouts.
3. Confirm graceful startup diagnostics and actionable recovery instructions; do not silently reset or overwrite learner data.
4. Check concurrency assumptions for one local user and multiple browser tabs. Do not claim multi-user concurrency.
5. Add bounded performance checks for startup, curriculum loading, progress queries, backup/restore, and representative audio processing on the target laptop.
6. Review logs for privacy leakage and ensure logs are useful without recording learner content unnecessarily.

**K5. Security verification and acceptance**
- Automated tests cover API validation, origin/host restrictions, security headers, import abuse, migration, backup/restore, deletion, and failure recovery.
- Run the repository's dependency audit and review all findings.
- Perform a documented manual security review of the local application and its filesystem/data permissions.
- If external penetration testing is unavailable at ₹0, state that clearly; do not call the app penetration-tested or certified.
- Create a security/privacy acceptance record with findings, severity, remediation, residual risks, and sign-off date.

**Phase K deliverables**
- Threat model and trust-boundary diagram/record.
- Data inventory, privacy notice, retention/deletion/export policy.
- API/security review and regression tests.
- Dependency/licence audit and documented exceptions.
- Backup/recovery and local reliability test record.
- Explicit supported/unsupported deployment boundary and residual-risk register.

**Phase K exit gate:** no unresolved critical/high-severity issue is knowingly shipped; remaining risks are documented and accepted for the local single-user release. Data export, deletion, restore, migrations, and failure recovery are tested. Dependency and licence checks are recorded. The app remains loopback-only unless a separate public/multi-user architecture, threat model, authentication, and privacy review are approved. Passing this gate is not a security certification.

---

### Phase L — Release Candidate, Packaging, Documentation & Operations

**Purpose:** produce a reproducible, maintainable release candidate that another person can install and use locally, recover from failures, and evaluate without relying on undocumented steps or developer-specific state. This is a local release-candidate goal, not an automatic commitment to public cloud deployment or Duolingo-scale operations.

**L0. Release definition and scope**
1. Define the supported release target(s), initially the developer's Linux/Omarchy environment and any additional platform only after it is actually tested.
2. Define the release audience and supported mode: local single-user, loopback-only, optional local voice engines, optional explicitly configured remote STT.
3. Publish a feature matrix separating required core functionality, optional voice dependencies, unsupported configurations, and known limitations.
4. Freeze scope for the release candidate. New features after the freeze require a material bug, security issue, or explicit scope decision.
5. Define versioning, changelog, migration policy, compatibility policy, and a reproducible release checklist.

**L1. Installation and packaging**
1. Make fresh installation reproducible from a clean checkout using documented Python and system prerequisites.
2. Provide a single clear setup/start/stop/update workflow consistent with the existing project conventions; avoid introducing a service manager or packaging framework without need.
3. Validate virtual-environment creation, dependency installation, static asset availability, curriculum validation, database initialisation, and readiness checks.
4. Keep local speech model installation explicit and optional. Do not download large model weights on application startup.
5. Document supported browser/device combinations based on actual tests, not assumptions.
6. Consider a simple local launcher or OS package only if it materially improves installation and does not add recurring cost or a heavy dependency.
7. Verify clean uninstall/update behaviour and explain which learner data is retained or removed.

**L2. Runtime operations and observability**
1. Provide concise startup diagnostics and a readiness check that covers database integrity, schema version, required tables, curriculum validity, and configured optional engines.
2. Use structured, local logs with timestamps and severity. Avoid storing answer text, transcripts, audio, API keys, or sensitive profile fields in logs.
3. Document common failures and recovery: missing dependencies, unavailable microphone, model not installed, TTS failure, database locked/corrupt, failed migration, invalid backup, and disk-space problems.
4. Define safe update behaviour and a backup-before-migration recommendation. Never silently replace a learner database.
5. Record basic resource observations on the target laptop: startup time, idle/active memory, representative lesson and progress queries, and optional voice processing. Report measurement conditions; do not call one-off measurements benchmarks.
6. No hosted telemetry, paid monitoring, analytics SDK, or background service is required. Any optional diagnostic export must be learner-initiated and scrubbed.

**L3. Data portability and recovery operations**
1. Finalise backup format documentation and compatibility guarantees for supported versions.
2. Provide a clear backup-before-update and restore-from-backup procedure, with a warning that restore replaces current learner data.
3. Run a full recovery drill on disposable data after a fresh install, including corrupted/invalid backup rejection and database integrity verification.
4. Verify that learner data survives application upgrades and that downgrade limitations are documented.
5. Explain where database, backups, logs, and model files live, and how the learner can move or delete them.

**L4. Release quality and demonstration**
1. Run the full automated suite, browser acceptance, Python compilation, JavaScript syntax checks, dependency audit, and clean-install test against the exact release commit.
2. Run the complete manual acceptance checklist on each claimed supported platform/device. Include keyboard, screen reader, contrast, zoom, narrow-screen, microphone permission, STT/TTS, text fallback, and recovery.
3. Prepare a deterministic demo script that works offline in text mode and identifies which optional voice features require local models or explicit remote configuration.
4. Prepare a product guide, installation guide, troubleshooting guide, privacy/data guide, architecture overview, known-limitations list, and change log.
5. Record test environment, commit SHA, commands, pass/fail/skip counts, manual findings, and unresolved issues.
6. Have a release review that checks scope, evidence, security residual risks, accessibility, documentation, and recovery readiness.

**L5. Deployment boundary and future hosting decision**
1. The default Phase L target is a local release candidate. No public hosting, LAN exposure, reverse proxy, tunnel, or multi-user service is enabled by this roadmap.
2. A future public deployment requires a separate approved phase/decision: explicit cost model, authentication and account recovery, multi-user isolation, hosted database and backups, abuse controls, HTTPS, monitoring, incident response, privacy/legal review, and an operations owner.
3. If those requirements cannot be met within the ₹0 constraint, keep the supported release local and document the limitation rather than quietly adding paid dependencies.
4. Do not use Duolingo-scale availability, concurrency, security, content volume, or learning outcomes as acceptance criteria for this local project.

**Phase L deliverables**
- Versioned local release candidate and changelog.
- Reproducible clean-install/update/uninstall instructions.
- Supported-platform and optional-dependency matrix.
- Readiness diagnostics, privacy-safe logs, troubleshooting and recovery guides.
- Verified backup/restore drill and upgrade compatibility record.
- Complete automated and manual release acceptance evidence.
- Demo script, product documentation, known limitations, and release sign-off.

**Phase L exit gate:** a new clean environment on each claimed supported platform can install and run the app using documented steps; the core learning journey works without paid services or external accounts; optional voice behaviour is explicit and recoverable; backup/restore and upgrade paths pass a documented drill; the exact release commit passes automated checks and manual acceptance; known risks and unsupported deployment modes are clearly stated. Only then may the project be called a local release candidate—not a mature commercial platform or a production-scale service.

---

### Cross-phase completion rules for I–L

1. **Sequential implementation with explicit deferrals:** complete a phase implementation, tests, and documentation before moving on. With explicit user approval, the next phase may begin while non-blocking hardware or participant acceptance from the previous phase is deferred; the earlier phase remains open and must not be described as accepted until its own exit gate is met.
2. **No speculative expansion:** do not add avatars, real-time streaming, always-on microphones, emotion analysis, pronunciation scoring, institution dashboards, mobile apps, cloud accounts, or generated curriculum unless a separate evidence-backed decision justifies them.
3. **No scope laundering:** a feature is not complete because a UI exists, a mock works, a unit test passes, or a provider reports available. Require end-to-end evidence and manual acceptance where hardware or learner behaviour matters.
4. **Preserve working behaviour:** protect existing text practice, session history, curriculum, Memory, Career, Progress, backup/restore, and Phase H evidence semantics with regression tests.
5. **Keep research separate from engineering:** a learner study can be optional when participants are unavailable; never fabricate findings or block engineering on a study that cannot yet be run.
6. **Report honestly:** every phase report must list what shipped, exact commit and CI run, tests and skips, manual checks, limitations, and deferred work.
7. **Release is a gate, not a promise:** failure to meet an exit criterion means the phase remains open. A strong local release candidate is a valid outcome under the zero-cost constraint; public production hosting is not assumed.


## Phase K implementation update (2026-11-20)

Phase K's engineering slice is now present on feature/learner-profile: loopback peer validation in addition to Host checks, bounded API request bodies with dedicated voice/restore limits, private default SQLite file permissions, symlink/non-regular DB rejection, privacy-safe voice exception logging, rollback and cascade tests, threat model, personal-data lifecycle inventory, backup encryption decision, and CI vulnerability/licence inventory artifacts.

This does not close Phase K yet. Exact-commit local tests and GitHub Actions must pass; the generated vulnerability/licence artifacts must be reviewed; and disposable-data disk-full, permission-denied, interrupted-restore, and schema-upgrade rehearsals remain manual acceptance items. See [Phase K Acceptance](PHASE_K_ACCEPTANCE.md).
