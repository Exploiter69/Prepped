# Prepped — Complete Project Roadmap

**Status:** Active engineering roadmap for a voice-first practice platform. The text MVP is frozen except for material bugs.<br>
**Updated:** 2026-11-19<br>
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

## 2. Current baseline and truth reset

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

The feature branch now has GitHub Actions coverage for pushes to `feature/**`. The latest clean-run result is 39 passed and 2 skipped (both require `espeak-ng`, unavailable on the hosted runner), with one Starlette/httpx TestClient deprecation warning. The [Foundation Acceptance Checklist](ACCEPTANCE_CHECKLIST.md) records the remaining real-browser profile, text-practice, and optional voice checks. Do not treat CI as browser or microphone acceptance.

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

## 7. Phase 2 — First voice slice (current milestone)

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

## 8. Phase 3 — Voice hardening and target-device acceptance (next)

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

## 10. Phase 5 — Personalisation and learning loop (future)

**Purpose:** move from one-off practice toward a personalised learning platform without turning uncertain model output into learner traits.

Only start after the voice loop is usable and user value is demonstrated.

Candidate steps:

- Turn concrete, evidence-linked weaknesses into learner-controlled review items.
- Link every item to the source answer and explain why it was suggested.
- Let the learner accept, edit, or reject items.
- Deduplicate items and track whether they are used in later attempts.
- Consider a simple local review schedule; FSRS remains a later experiment.
- Consider a local-only model adapter for wording or scenario variation, behind a narrow validated interface, with deterministic fallback.
- Keep assessment off the realtime path.

**Exit gate:** review items are accurate, useful, non-duplicative, and reused. If they are noisy, keep a manual/rules-based list or stop.

## 11. Phase 6 — Second scenario and fluency practice (future)

**Purpose:** prove the scenario/voice layer generalises without becoming a generic platform.

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

## 17. Immediate next actions

1. **Complete browser/microphone acceptance** using the checklist in [VOICE.md](VOICE.md) on the target laptop. Record actual results, including failures.
2. **Run GitHub Actions** on the pushed voice commit; fix any CI issue before merge.
3. **Run a fresh-checkout setup** with `.[dev]`, then voice setup, and confirm text mode still works without models.
4. **Record voice observations** (latency, memory, transcript errors) with the method and environment; do not call them benchmarks yet.
5. **Decide Phase 3 scope from observed failures**, not from novelty. Keep text fallback and editing mandatory.
6. **Run user validation only when feasible.** It is valuable, but it is not a blocker for engineering.

**Current gate:** record/stop slice and mocked Groq adapter implemented; live provider, real browser/microphone acceptance, and CI are outstanding. Speech accuracy and learning outcomes are not validated and must not be claimed.


---

## 18. Updated product completion plan (2026-11-19)

This section is the active execution order for turning the current practice foundation into the complete learning product. It refines the earlier future-work phases: the learner profile now exists, so the next product milestone is to make it drive a real learning experience. The earlier Phase 5/6 ideas remain valid, but implementation must follow the gates below.

### Current truth

- The app has one project-explanation practice scenario, a local session/history flow, heuristic formative feedback, a bounded voice record/stop slice, and a learner profile.
- The profile stores preferences. It does not yet generate adaptive lessons or profile-driven recommendations.
- The app does not yet contain a structured English curriculum, general lesson runner, vocabulary revision system, spaced repetition, comprehensive progress insights, or backup/restore.
- The profile button fix has been pushed to the feature branch, but browser acceptance must be confirmed locally.
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
| G | Release hardening | Accessibility, security, performance, fresh install and usability evidence | Release checklist and documented limitations |

### Milestone B — Learning Engine detailed tasks

1. Define a stable skill taxonomy with skill IDs, learning outcomes, and prerequisites.
2. Define a versioned JSON curriculum format for tracks, units, lessons, exercises, and content references.
3. Validate curriculum files and reject unknown skill IDs, broken prerequisites, missing content, and invalid exercise schemas.
4. Implement a reusable lesson/session runner with explicit states: introduction, example, exercise, response, feedback, retry, completion.
5. Add deterministic exercise types first: sentence ordering/construction, grammar-in-context, vocabulary-in-context, short response, and listening comprehension.
6. Persist attempts, completion, skill links, timestamps, and feedback evidence in SQLite using additive migrations.
7. Connect profile goals and improvement areas to a transparent starter-path selector. Show the reason for each suggested lesson and let learners override it.
8. Add a short baseline diagnostic only after the exercises and feedback are stable; it is formative, not a certified language level.
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

- Save items only through learner action or explicit acceptance.
- Store the original response/source context and why an item was suggested.
- Support edit, delete, dismiss, suspend, and duplicate handling.
- Add a simple local due-date scheduler only after review-card usefulness is demonstrated.
- Test due-date boundaries, repeated reviews, persistence, and deletion.

### Milestone E — Career and interview studios

- Reuse the lesson/scenario runner and existing voice/session APIs.
- Add project explanation and contribution, HR/behavioural, and technical interview tracks.
- Add explicit multi-turn follow-up states and bounded scenario completion.
- Keep feedback tied to submitted answers and rubric versions.
- Add role-specific content only when authored and covered by tests.

### Milestone F/G — Progress, portability, and release

- Progress is based on completed work and explainable evidence, never an unexplained single score.
- Show goals, activity, skill practice, review completion, and recommendation reasons.
- Implement local export, backup, restore, and recovery tests.
- Complete keyboard, responsive, focus, contrast, and screen-reader checks.
- Review security, dependency health, local data handling, and audio upload boundaries.
- Test a fresh clone/install on the target laptop.
- Complete manual acceptance for onboarding, lessons, voice/text practice, review, progress, and recovery.
- Run a small consent-based usability study when practical; report method and sample size without claiming causal learning or placement impact.

### Release readiness checklist

A release candidate requires all of the following:
- [ ] Every advertised core module has a complete end-to-end learner flow.
- [ ] Profile choices actually affect the learning path and recommendations.
- [ ] English curriculum contains complete, tested learning units.
- [ ] Learner memory and revision work end to end.
- [ ] Interview scenarios reuse the common engine.
- [ ] Progress is evidence-based and understandable.
- [ ] Export/backup/restore has been tested.
- [ ] Automated tests and CI pass on the release commit.
- [ ] Fresh-install and target-device checks pass.
- [ ] Accessibility, privacy, security, and failure states are reviewed.
- [ ] Claims and limitations match demonstrated evidence.

A student usability pilot is useful evidence but does not block engineering. A release must not claim certified English proficiency, accurate pronunciation scoring, placement probability, or measured learning gains without separate validation.
