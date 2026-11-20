# Prepped — Complete Project Roadmap

**Status:** Active roadmap. Phases A–F are implemented on `feature/learner-profile`; Phase G is the not-yet-started release-hardening and acceptance milestone. The text MVP is frozen except for material bugs.<br>
**Updated:** 2026-11-20<br>
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

The feature branch now has GitHub Actions coverage for pushes to `feature/**`. The current full-suite result is [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped (both require `espeak-ng`, unavailable on the hosted runner), with one Starlette/httpx TestClient deprecation warning. Playwright/Chromium browser tests passed for profile setup/edit/cancel/save/reload and the full text-only practice journey. The [Foundation Acceptance Checklist](ACCEPTANCE_CHECKLIST.md) records the remaining target-laptop and optional voice checks. Do not treat headless CI as microphone or device acceptance.

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

## 17. Pre-Phase-G completion gates (updated 2026-11-20)

1. **Automated verification is green:** [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning; compilation, JavaScript syntax, dependency audit, API tests, and Chromium acceptance passed.
2. **Complete manual target-laptop acceptance** for Phases A–F using [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md), including browser, microphone/STT/TTS, keyboard, screen-reader, contrast, responsive, and data-recovery checks.
3. **Complete a clean install and recovery rehearsal** on the target Omarchy laptop using [INSTALL.md](INSTALL.md), with backups tested only against disposable data.
4. **Review limitations and evidence**; do not claim speech accuracy, proficiency, learning gains, placement outcomes, or security certification without validation.
5. **Keep the optional student pilot separate** from engineering. Run it only with consent and available participants; no results are currently claimed.

**Current gate:** Phases A–F implementation and automated verification are complete on the working branch. Manual target-device acceptance remains open. Phase G has not started.


---

## 18. Updated product completion plan (2026-11-19)

This is the authoritative A–G execution sequence. Earlier sections are the original research/planning model and historical baseline; use this section plus CURRENT_STATE.md for present implementation truth. Phases A–F are implemented; Phase G is deliberately held until the pre-release manual acceptance gates are complete.

### Current truth

- The app has the original project-explanation practice scenario, a local session/history flow, formative feedback, a bounded voice record/stop slice, a learner profile, and a reusable Learning Engine.
- The profile goal and focus areas select transparent starter routes through the versioned curriculum; they do not infer ability or adapt difficulty.
- The branch now contains the initial English and communication curriculum, learner-controlled memory and spaced revision, three interview studios, and the Phase F progress/goals/backup/restore workspace. Target-device acceptance for Phases D–F remains outstanding.
- Latest full CI is green: [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning. Target-device acceptance for Phases A–F remains outstanding.
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
| G | Release hardening and acceptance (not started) | Target-device, accessibility, privacy/security, performance, fresh-install and release-candidate verification | Manual acceptance record, green CI, recovery rehearsal, limitations and release checklist |

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
- [x] Final automated CI pass for the current implementation commit: [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning.
- [ ] Complete target-laptop progress and data-recovery acceptance.

### Milestone G — Release hardening and validation

Phase F implements the initial hardening foundations: local Host/Origin checks, security headers/CSP, readiness checks, dependency audit in CI, and clean-install/recovery/security documentation. The remaining G/release-candidate work is target-device acceptance, keyboard/screen-reader/contrast review, any necessary security/dependency remediation, performance observations, and optional consent-based usability validation. No public/multi-user deployment is supported. Do not invent pilot results.

### Release readiness checklist

A release candidate requires all of the following:
- [ ] Every advertised core module has a complete end-to-end learner flow.
- [ ] Profile choices actually affect the learning path and recommendations.
- [ ] English curriculum contains complete, tested learning units.
- [ ] Learner memory and revision work end to end.
- [ ] Interview scenarios reuse the common engine.
- [x] Progress is evidence-based and understandable in the implementation; target-device acceptance remains pending.
- [x] Export/backup/restore is implemented with API round-trip and failure-path tests; target-device acceptance remains pending.
- [ ] Automated tests and CI pass on the final Phase F implementation commit.
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

Automated API and Chromium coverage for curriculum inventory, profile focus routing, question/grammar/vocabulary handling, listening alternatives, and pronunciation self-review passes in [the current full-suite CI run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427). Target-laptop browser, audio, microphone/STT disclosure, transcript-editing, keyboard, and responsive acceptance remain manual gates.

The Phase C implementation does not claim certified English proficiency, pronunciation accuracy, improved learning outcomes, or hiring/placement probability. Open speaking responses are retained as learner work and are not automatically graded.

A student usability pilot is useful evidence but does not block engineering. A release must not claim certified English proficiency, accurate pronunciation scoring, placement probability, or measured learning gains without separate validation.

## 19. Phase B — Learning Engine implementation update (2026-11-19)

The first reusable learning-engine slice has been committed to feature/learner-profile. It adds a versioned local curriculum manifest, 14 stable skill definitions, one foundation level, nine units, four tracks, 13 authored lessons plus one diagnostic check, explicit outcomes and prerequisites, and seven exercise formats: choice, ordering, vocabulary, listening, short response, reflection, and pronunciation.

The FastAPI learning router validates the manifest and provides catalogue, recommendations, attempt start/read/response, and progress endpoints. The lesson runner enforces exercise order and prerequisite completion, keeps answer keys out of public catalogue/active exercise payloads, persists responses and feedback, and allows in-progress attempts to resume after restart. Additive SQLite attempt/event tables preserve all existing practice and profile records.

Profile goal/focus preferences select a transparent route with per-lesson reasons. The browser workspace supports skill and unit browsing, recommended lessons, all seven exercise formats, local TTS listening and pronunciation playback with text alternatives, optional STT responses, next-lesson navigation, response feedback, progress counts, and resuming unfinished lessons. Choice and ordering items have deterministic answer feedback; open responses are saved for self-review without automatic grading or proficiency claims.

Automated API and Chromium tests have been added. This implementation is included in the green [full-suite CI run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427). Target-laptop browser acceptance remains a separate open gate. A low-stakes starting-point check is included. It records sentence, ordering, listening, and project-response tasks; attempts can be repeated and reviewed. It assigns no proficiency level or overall score. More advanced diagnostic interpretation remains future work. Dedicated HR, project, and technical interview studios are now implemented under Phase E. Learner-controlled revision is implemented under Phase D; its automated and target-laptop acceptance gates remain open.


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

The Career workspace is implemented on `feature/learner-profile`. The current full-suite GitHub Actions run [44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) passes 100 tests with 2 optional `espeak-ng` skips and 1 warning. Target-laptop acceptance remains outstanding.

- Three versioned studios: project explanation, HR/behavioural interviews, and technical fundamentals.
- Four authored main questions per studio, each followed by an authored follow-up. Guided, standard, and challenging modes choose different follow-up wording.
- FastAPI interview session APIs with ordered turns, persisted session snapshots, resume, recent history, retry grouping, feedback, and deletion.
- Additive `career_sessions` and `career_turns` tables; existing practice sessions, learner profile, curriculum attempts/events, and Phase D memory are preserved.
- Browser workspace supports typed answers, record/stop transcription through the existing voice adapter, editable transcripts, and spoken prompts through existing local TTS. Text remains available when voice is unavailable.
- Groq transcription disclosure is shown before requesting microphone permission when the configured STT engine is Groq. Raw recordings are not stored by Prepped.
- Question-by-question reflection uses transparent text signals and exact answer evidence. It does not claim technical correctness, expert recruiter evaluation, interview success, or placement probability.
- Learners can explicitly send an answer into the Phase D memory editor with its question/session source context. The learner must review and submit the item; no automatic memory writes occur.

The automated suite covers the API state machine, all studio content, difficulty-specific follow-ups, persistence, retry, deletion cascade, legacy practice preservation, browser completion/resume/review, and the memory handoff. The full current implementation suite passes in [CI run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427); target-laptop acceptance remains open before Phase E can be called fully accepted.


---

## Phase F — Progress, portability, and hardening foundations (2026-11-20)

Phase F is implemented on `feature/learner-profile`. The complete current CI workflow passes on [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427): 100 passed, 2 skipped, 1 warning. The workflow completed Python compilation, all six JavaScript syntax checks, dependency installation, `pip-audit`, Chromium installation, API tests, and browser acceptance.

Delivered: evidence-linked skill/activity progress; learner-owned goals; explainable recommendations with persistent dismiss/restore; JSON export and staged full-replacement restore covering every learner-data table; schema/format version checks; local Host/Origin restrictions; security headers/CSP; readiness checks; and install/recovery/security documentation.

**Still open:** target-laptop acceptance for all A–F learner journeys, fresh-install/recovery rehearsal, voice hardware/provider checks, keyboard/screen-reader/contrast/responsive review, and any fixes arising from those checks. The two CI skips require `espeak-ng` and are not counted as passes. The student pilot remains optional future validation, not a prerequisite to engineering.

**Phase G has not started.** It is reserved for closing the release-hardening and acceptance gates after the manual A–F evidence is recorded.
