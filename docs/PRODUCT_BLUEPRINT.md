# Prepped — Complete Product and System Blueprint

**Version:** 2.1 — voice-first direction<br>
**Status:** Active direction. The text loop is implemented and frozen except material bugs; the first record/stop voice slice and optional Groq STT adapter are implemented, with live acceptance outstanding.<br>
**Last updated:** 2026-11-04<br>
**Repository:** Exploiter69/Prepped<br>
**Companion documents:** [Current State](CURRENT_STATE.md) · [Complete Roadmap](COMPLETE_ROADMAP.md) · [Voice Setup](VOICE.md) · [ADR-002](ADR-002-LOCAL-VOICE-SLICE.md) · [Research Decision Matrix](RESEARCH_DECISION_MATRIX.md)

## 1. Product definition

**Prepped is a voice-first, personalised practice and learning environment for Indian engineering students: placement preparation, professional communication, English fluency, and technical interview practice.**

The first implemented slice lets a learner speak an answer to a project-interview prompt, correct the local transcript, and submit it through the same session loop as typed text. Prepped is a structured practice environment, not a general-purpose chatbot, an official university service, a hiring tool, a placement predictor, or a validated speech-accuracy product.

### The problem

Students may understand their projects and technical subjects but still find it difficult to explain their contribution, organise an answer, support claims with concrete examples, or respond to follow-up questions under pressure. Practising in front of peers or mentors can feel embarrassing, while generic chat does not guarantee realistic scenarios or useful feedback.

Prepped offers a private, repeatable way to practise a defined conversation, review the answer, and try again with a clear next step.

### Primary user

Indian college engineering students preparing for placements, internships, project reviews, and early-career professional communication.

### First job to be done

“Help me practise explaining my project and answering follow-up questions before a real placement interview.”

### First scenario

**Explain your project to a placement interviewer.**

The simulated interviewer asks a small number of follow-ups about the problem, the learner's role, design decisions, evidence/results, and lessons learned. Questions should respond to the learner's actual answers rather than follow a long fixed script.

English is the first practice language. Use clear, natural language and avoid claiming support for every Indian accent or language until it has been tested.

## 2. Product principles

1. **Practice a real task:** each session has a clear scenario, role, goal, and ending.
2. **Evidence before judgement:** feedback must point to words or actions present in the session.
3. **Action over scores:** give a concrete next step, not an unexplained number.
4. **Retry is central:** the learner can try again using the same rubric.
5. **Deterministic control:** application code owns scenario state and allowed transitions; an LLM cannot decide its own permissions.
6. **Local-first by default:** the core demo must run without a paid API, subscription, hosted database, or paid deployment.
7. **Privacy is a feature:** collect little data, do not store raw audio by default, and provide deletion for stored sessions.
8. **Accessible alternatives:** text interaction, readable transcripts, keyboard use, and clear error states are first-class.
9. **Evidence-led scope:** features are added because tests or users justify them, not because a research report lists them.
10. **Honest claims:** clearly distinguish proposed, implemented, tested, and observed outcomes.

## 3. The first release and its boundaries

### Included and implemented

- One curated project-explanation interview scenario.
- A short guided conversation with a small number of relevant follow-up questions.
- Text input and responses.
- Browser microphone capture with explicit **Start recording** / **Stop recording**.
- Editable transcript before submission, using optional Groq Whisper or local Vosk.
- Submission of the corrected transcript through the existing session backend.
- Local Piper text-to-speech for interviewer prompts, with `espeak-ng` fallback.
- **Play**, **Stop**, and **Replay** controls for spoken prompts.
- Clear microphone/model/TTS errors and a working text fallback.
- Ordered session transcript/answer history.
- Transparent checklist feedback with evidence from the learner's actual answer.
- Retry, attempt comparison, local session history, and explicit deletion.
- Automated tests for scenario flow, voice boundaries, failure handling, feedback grounding, retry consistency, and deletion.
- No raw audio persistence by default.

### Explicitly excluded from this phase

- Required paid APIs, temporary free-credit dependencies, paid hosting, or hosted database services.
- Mandatory login, institution accounts, SSO, LMS integration, or multi-tenant cloud.
- Public social feeds, profiles, community posts, marketplace, or peer ranking.
- Multiple agents, a general-purpose graph platform, or a complex workflow engine.
- Avatars, animated faces, viseme/lip-sync, VR, or virtual worlds.
- Emotion detection, personality inference, automated confidence scoring, or employability judgements.
- Phoneme-level pronunciation scores, IELTS/ACTFL certification, or a single overall “communication score.”
- Predictive placement modelling or any unsupported percentage-improvement claim.
- Always-listening recording, realtime streaming agents, interruption/VAD orchestration, or raw-audio retention by default.
- LLM feedback, adaptive intelligence, or personalisation in the current voice milestone.
- Additional phrase heuristics in the existing text feedback engine.

These exclusions are intentional scope control, not a statement that the features can never be considered.

## 4. Core learner experience

### Flow A — first attempt

1. **Welcome:** explain that this is a practice prototype and not an official assessment.
2. **Scenario briefing:** explain the interviewer role, task, approximate length, and what the learner should prepare.
3. **Start:** create a local session and show the first interviewer question.
4. **Answer:** learner types a response or records a spoken answer, reviews the local transcript, corrects errors, and saves through the same backend.
5. **Follow-up:** deterministic scenario logic chooses a relevant next question using explicit state and simple validated rules. Optional model-generated wording may be used only behind validation.
6. **Finish:** the learner can finish early or complete the bounded scenario.
7. **Review:** show the learner's answers and the checklist feedback.
8. **Retry:** learner tries the same scenario again.
9. **Compare:** show the two attempts and their checklist criteria side by side.
10. **Delete:** learner can remove saved session data.

### Flow B — feedback review

Every feedback item contains:

- Criterion name.
- Observed evidence from the actual answer.
- Plain-language explanation of what worked or what is missing.
- One concrete action or example to try next.
- An uncertainty state when the answer does not provide enough evidence.

Do not quote fabricated text. Do not infer intelligence, personality, confidence, empathy, or hiring potential from a single response. A better second answer is an observed difference in this task, not proof of general employability improvement.

### Flow C — first voice slice (implemented)

The current flow is microphone permission → record/stop → transcription through the configured STT provider → editable transcript → submission through the existing answer endpoint → feedback. Vosk transcription and interviewer prompts run locally; optional Groq Whisper sends recorded audio to Groq. The UI discloses the active STT mode. Text remains available when microphone access, transcription, decoding, or TTS fails.

This is a bounded record/stop interaction, not an always-listening realtime agent. Speech accuracy is not validated; the transcript must remain inspectable and correctable.

## 5. Initial feedback rubric

The initial rubric is formative and checklist-based. It is not a validated psychometric instrument.

| Criterion | Observable question | Example evidence |
|---|---|---|
| **Clarity** | Can a listener understand the project's purpose? | The answer explains the problem in plain language |
| **Structure** | Does the answer cover the key parts in a logical order? | Problem, approach, personal contribution, result |
| **Specificity** | Does the learner give concrete details rather than unsupported claims? | A named component, decision, constraint, or result |
| **Question coverage (implemented)** | Has each prompt received a non-empty response? | A completion count across the five scenario prompts |
| **Follow-up handling (not implemented)** | Does the answer address a follow-up question actually asked? | Requires a scenario with explicit follow-up turns; the current scenario has none |
| **Conciseness** | Is the answer relevant without omitting important context? | Avoids repetition while retaining necessary detail |

Each criterion may be marked as **evident**, **partly evident**, or **not enough evidence**. Use these labels as guidance, not as calibrated scores. The exact wording and examples should be reviewed by the team and, if possible, a faculty member before the pilot.

### Feedback generation policy

- First choice: transparent deterministic checks and a small curated feedback library.
- Optional local LLM: may suggest wording or a revision, but the output must be checked against the learner's actual answer and the allowed feedback schema.
- If model output is malformed, unsupported, or unavailable: fall back to deterministic feedback and tell the learner when a richer suggestion could not be generated.
- Keep feedback generation separate from the interviewer persona. The interviewer should not expose the full rubric while roleplaying.
- Record scenario/rubric versions with each session so comparisons remain meaningful.

## 6. System architecture for the first implementation

Use one local-first modular application. The design should be simple enough for the student team to understand, test, and explain.

### Chosen first stack

| Layer | Choice | Responsibility |
|---|---|---|
| Application/backend | Python + FastAPI | Serves the interface and handles session operations |
| Interface | Plain HTML, CSS, JavaScript | Scenario screens, answers, transcript, feedback, retry, comparison |
| Local data | SQLite | Session metadata, turns/answers, feedback result, deletion |
| Scenario content | Versioned JSON files | Questions, roles, states, transitions, and completion rules |
| Scenario controller | Small deterministic Python module | Owns state, validates transitions, decides next allowed question |
| Feedback | Explicit rubric and validated structured output | Produces evidence-linked coaching |
| Optional model | Local model adapter, such as an Ollama-compatible endpoint | Provides alternative wording or follow-up phrasing if available |
| Tests | pytest or Python standard testing tools | Verifies core behaviour and failure handling |
| Source of truth | GitHub repository | Code, docs, scenario versions, tests, decisions, and evidence |

The optional model adapter is an interface, not a commitment to one model. The app should start and complete the deterministic scenario even if the local model is not installed or running.

### Logical modules

1. **Scenario catalog:** loads and validates scenario JSON.
2. **Session controller:** starts, advances, ends, and retries sessions.
3. **Question selector:** selects the next allowed interviewer question based on scenario state and validated answer signals.
4. **Answer store:** saves ordered turns for local review.
5. **Feedback engine:** applies the rubric and associates each feedback item with answer evidence.
6. **Attempt comparison:** compares two sessions against the same rubric version.
7. **Privacy/data controls:** deletes selected session data and associated feedback.
8. **Optional model adapter:** generates suggestions only through a narrow, validated interface.
9. **Test/evaluation fixtures:** known answers, edge cases, expected transitions, and feedback-grounding checks.

Do not create separate services or deployment units for these modules. Keep them as clearly named parts of one application.

### Scenario state model

The first scenario can use states such as:

- Introduction
- Project purpose
- Learner contribution
- Design decision
- Result/evidence
- Follow-up challenge
- Learner question / closing
- Completed

Transitions are explicit. A state has a goal, a question or allowed question set, and a next state or terminal condition. A model may help phrase a question, but it cannot create arbitrary states, bypass completion rules, or change permissions.

### Conceptual data model

| Record | Minimum information | Reason |
|---|---|---|
| Scenario definition | ID, version, title, role, state list, transitions, rubric reference | Reproducible scenario flow |
| Session | ID, scenario version, start/end time, status | Session lifecycle |
| Turn/answer | Session ID, sequence, speaker, text, timestamp/order | Transcript and evidence |
| Feedback item | Session ID, rubric version, criterion, evidence reference, explanation, next action | Grounded feedback |
| Attempt comparison | Session IDs and shared rubric version | Consistent retry review |

Avoid storing unnecessary identity, demographic, placement, health, or sensitive information. The first local demo does not need institutional or user-profile tables.

## 7. Optional model integration contract

The app must not require a model to function. If a local model is enabled, keep its responsibility narrow:

- Input: scenario-safe context, the current question/state, and learner answer text.
- Output: a schema-validated suggestion such as a candidate follow-up question or a rewritten example.
- Forbidden: SQL, direct database access, file access, permission changes, arbitrary scenario transitions, hidden system configuration, or unsupported score claims.
- Validation: check output shape, length, relevance to current state, and evidence references.
- Failure: one bounded retry at most, then deterministic fallback.
- Provenance: record whether a response was deterministic or model-assisted, along with the model/prompt version when available.

The application controller remains the authority. Treat all learner text and model output as untrusted input.

## 8. Privacy, safety, and trust

### MVP defaults

- Local-only operation by default; optional remote transcription is explicitly enabled by the developer and disclosed to the learner.
- No raw audio persistence by default. The first voice slice decodes and transcribes in memory; only corrected answer text is stored.
- Explain what is saved and why.
- Provide session deletion and test it.
- Do not transmit learner answers to external services. If optional remote STT is enabled, only the audio recording is sent for transcription; the corrected answer is stored locally.
- Do not collect personal identifiers that are not required for the practice task.
- Do not use session content for model training.
- Show a clear notice that the interviewer is simulated.
- Provide a stop/end action at all times.
- Avoid roleplay that pressures users to reveal sensitive personal information.

### Voice requirements (first slice implemented)

- Explicit microphone permission.
- Record/stop control; no always-listening mode.
- STT with an editable transcript before submission (Groq Whisper opt-in; Vosk offline fallback).
- Local TTS prompt playback with stop/replay.
- Text captions and an alternative text interaction.
- Visible recording, transcription, and failure states.
- No raw audio retention by default.
- No voice cloning.
- No emotion/personality inference.
- A documented retention/deletion policy before any external validation.

### Legal note

Privacy and child-data obligations depend on the launch context and current law. The AI reports are not legal advice. Before processing data from minors or launching a public service, review current requirements with an appropriate qualified person. A local student prototype should minimise data and avoid collecting under-18 user data unless the team has a clear approved process.

## 9. Accessibility and usability

Include from the beginning:

- Readable typography, contrast, and responsive layout.
- Keyboard navigation for the entire text flow.
- Clear focus states and labels.
- No reliance on colour alone to communicate feedback.
- A text-only path for every scenario.
- Clear loading, empty, error, and completion states.
- An easy-to-find stop, restart, retry, and delete action.
- For voice: visible microphone/recording state, editable transcript, spoken-prompt stop/replay, and graceful text fallback.

Target good accessibility practices from the first version; formal WCAG conformance should not be claimed without an appropriate audit.

## 10. Quality strategy

### Functional tests

- Scenario JSON validation.
- Valid state transitions and terminal completion.
- Question relevance for representative answer cases.
- Session ordering and persistence.
- Retry consistency with the same rubric version.
- Feedback evidence exists in the learner's actual answer.
- Invalid model output falls back safely.
- Empty/long/unexpected input handling.
- Session deletion removes all related local records.
- Voice boundaries: missing model/package, missing ffmpeg, empty/silent/oversized/undecodable audio, denied microphone, TTS failure, editable transcript, and text fallback.
- No raw audio file created by the transcription path.
- Fresh-checkout setup and smoke test.

### Feedback-quality tests

Create a small fixed set of representative answers:

- Clear and well-structured answer.
- Vague answer with no concrete contribution.
- Answer that makes a claim without evidence.
- Answer that does not address the follow-up.
- Very short answer with insufficient evidence.
- Prompt-injection attempt asking the model to ignore the scenario.
- Malformed or fabricated model output.

For each case, record expected behaviour and regressions. Automated tests can verify grounding and structure; human review is still required to judge whether feedback is understandable and useful.

### Future validation metrics (not an engineering blocker)

For a small pilot of 10–20 student volunteers if available, record:

- Completion without assistance.
- Confusing steps and bugs.
- Whether feedback cites actual answers.
- Whether the learner understands the next action.
- Change between first and second attempts using the same checklist.
- Voice-specific: microphone permission, record/stop, transcript correction, spoken-prompt stop/replay, and text fallback.
- Willingness to use it again.
- Time to complete and reported friction.

State the sample size and limitations. Do not claim causality, speech accuracy, or general placement impact from a small convenience sample. Engineering continues without waiting for this validation.

## 11. Voice architecture — local record/stop slice (implemented)

The voice slice is a bounded record/stop cascade with editable text in the middle. STT selection is opt-in:

```text
Browser MediaRecorder
  → POST /api/voice/transcribe (raw audio body)
  → ffmpeg decode in memory
  → Groq Whisper when configured, otherwise local Vosk STT
  → editable transcript in the existing answer textarea
  → existing POST /api/sessions/{id}/answers
```

Interviewer prompts use local Piper TTS, falling back to local `espeak-ng`. The question text is always visible.

### Engine choices

| Role | Chosen | Why | Limitations |
|---|---|---|---|
| STT (optional cloud) | Groq `whisper-large-v3` | Multilingual model, free-tier rate-limited access | Audio leaves device; target-speaker accuracy still needs evaluation |
| STT (offline fallback) | Vosk 0.3.45 + `vosk-model-small-en-us-0.15` | Apache 2.0, CPU-friendly, small, no cloud account | Known weak recognition for some Indian English speech; transcript remains editable |
| TTS | Piper 1.8.0 + `en_US-lessac-medium` | Local neural voice, CPU-compatible, better than formant synthesis | GPL-3.0-or-later; first load is slow; optional |
| TTS fallback | `espeak-ng` | Tiny, local, often preinstalled | Robotic voice |
| Decode | `ffmpeg` | Handles browser containers without temporary files | System dependency |

whisper.cpp remains a plausible future offline STT adapter. No realtime framework or paid speech provider is required.

### Rules

1. Record/stop only; no always-listening mode.
2. No model download at application startup. Setup is explicit.
3. No raw audio persistence by default; decode in memory.
4. Keep the transcript inspectable and correctable.
5. Submit through the existing session/answer backend.
6. Keep text fallback and clear errors.
7. Use a deterministic scenario controller; assessment stays outside the live voice path.
8. Report only measurements from the actual tested setup. One-off timings are not benchmarks, and speech accuracy is not claimed as validated.

See [Voice Setup](VOICE.md) and [ADR-002](ADR-002-LOCAL-VOICE-SLICE.md) for the implementation details and known limitations.

## 12. Learning loop beyond the first MVP

After feedback and retry prove useful, consider a review loop:

1. Identify a concrete weakness in a learner answer.
2. Propose a small review item tied to the source answer.
3. Let the learner accept, edit, or reject it.
4. Deduplicate similar items.
5. Reintroduce the skill in a later scenario.
6. Observe whether the learner applies the idea again.
7. Consider FSRS scheduling only after review-item quality and usefulness are demonstrated.

Candidate review items may include project explanation structure, missing evidence, concise phrasing, or handling a common follow-up. Do not automatically turn uncertain AI judgments into persistent learner traits.

## 13. Complete project phases

The detailed gates, tasks, semester map, testing plan, and deliverables live in the [Complete Roadmap](COMPLETE_ROADMAP.md). The overall order is:

1. **Foundation:** repository truth, scenario, rubric, local app skeleton.
2. **Text vertical slice:** scenario, answers, feedback, retry, comparison, deletion. Implemented and frozen except material bugs.
3. **First voice slice:** record/stop, optional Groq Whisper or Vosk STT, editable transcript, Piper/espeak TTS, failure fallback. Implemented; live provider and browser acceptance outstanding.
4. **Voice hardening:** browser/microphone acceptance, latency/accuracy observations, failure fixes.
5. **User validation:** usability and voice-specific findings when participants are available. Not an engineering blocker.
6. **Personalisation and review loop:** evidence-linked review items and later scheduling, only after voice value is demonstrated.
7. **Second scenario and fluency:** validate reusable scenario/voice structure.
8. **Human calibration:** evaluate rubric consistency before any score claims.
9. **Final-year options:** additional scenarios, language support, faculty/institution features, advanced audio, or avatars only when justified.

## 14. Feature priority by evidence gate

| Feature | Priority | Gate |
|---|---|---|
| One text project-interview scenario | Required | First runnable MVP |
| Evidence-linked checklist feedback | Required | First runnable MVP |
| Retry and attempt comparison | Required | First runnable MVP |
| Local history and deletion | Required | First runnable MVP |
| Optional local LLM | Not in this phase | Keep deterministic flow and text fallback stable |
| Voice input/output | Implemented first slice | Browser acceptance, accuracy observations, and failure handling |
| Review items | Later | Voice value, feedback quality, and student usefulness |
| FSRS | Later experiment | Review-item usefulness demonstrated |
| Second scenario | Later | Voice loop is usable and validation identifies a useful expansion |
| Pronunciation/GOP scoring | Research only initially | Audio benchmark and human validation |
| Numeric rubric score | Not in v1 | Human calibration and clear validity limits |
| Avatar/lip-sync/VR | Deferred | Evidence of learning benefit and feasible cost |
| Faculty dashboards / LMS / SSO | Deferred | Real stakeholder need, privacy basis, and capacity |
| Placement prediction / “40% improvement” | Not approved | Requires a properly designed study; no claim currently supported |

## 15. How research is used

The five AI reports are complementary, not a single authoritative specification:

- **Claude** informs boundaries, state control, evidence provenance, reliability, privacy, and testing; its production infrastructure is simplified.
- **Gemini Deep Research** informs scenario learning, local voice options, accessibility, FSRS and pronunciation-assessment hypotheses; its performance, pricing, and legal claims require verification.
- **DeepSeek** informs future voice-pipeline comparisons, streaming/interruption requirements, stage-level measurement, fallbacks, and human validation.
- **Grok** informs competitor hypotheses and potential differentiation; its image-based PDF limits exact transcription fidelity and its market claims need fresh verification.
- **Perplexity** informs the broader practice-feedback-review loop, accessibility, assessment validity, and future feature roadmap; its broad production stack is narrowed to the first student use case.

See the [Research Decision Matrix](RESEARCH_DECISION_MATRIX.md) for explicit adopted, deferred, rejected, and re-verification decisions. See the archive [verification report](../research/raw/VERIFICATION.md) for source fidelity.

## 16. Claim and evidence policy

Every project claim must be labelled correctly:

- **Proposed:** written in a plan but not built.
- **Implemented:** present in the code.
- **Tested:** a repeatable test verifies it; record test and environment.
- **Observed:** a pilot or experiment produced recorded results.
- **Externally reported:** supported by a named source and date.
- **Hypothesis:** plausible but not established.

Do not use AI-generated research as proof of implementation. Do not present the previous “40% improvement in readiness” statement as a result. Do not say Prepped measures confidence, personality, employability, or placement chances. Do not claim formal accessibility conformance, legal compliance, or validated assessment without the relevant review.

## 17. Current decision

**Keep the implemented text loop as a stable fallback. Build the voice-first product on the same simple app: record/stop microphone input, opt-in Groq Whisper or offline Vosk STT with an editable transcript, local TTS prompt playback, and submission through the existing session backend. Harden the browser/device experience next; user validation is valuable but is not an engineering blocker.**

Speech accuracy, latency, and learning outcomes are not validated. No LLM feedback, adaptive intelligence, pronunciation scoring, or overall score is added in this phase. Everything beyond the first voice slice remains a conditional expansion, not a prerequisite.

---

## 15. Product completion status and implementation plan (2026-11-19)

The blueprint describes the destination, not the current feature set. The current application is a local practice foundation with one project-explanation scenario, a bounded voice record/stop slice, formative heuristic feedback, history, and a learner profile. It is not yet a complete or market-ready learning platform.

The learner profile stores preferences; it does not yet drive adaptive lessons or personalised recommendations. The following capabilities remain future implementation: reusable lesson engine, skill taxonomy, versioned curriculum, English grammar/sentence/vocabulary/fluency/listening units, learner-controlled revision memory, spaced repetition, HR and technical interview studios, evidence-based progress, data export/backup/restore, and full release hardening.

Use [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) for the product-level phases, and [COMPLETE_ROADMAP.md](COMPLETE_ROADMAP.md) for milestone tasks, exit criteria, and release readiness. [CURRENT_STATE.md](CURRENT_STATE.md) records what is actually implemented and verified.

### Active build order

1. Stabilise and manually accept the existing profile, practice, and voice flows.
2. Build the Learning Engine: skill taxonomy, versioned local JSON curriculum, reusable lesson runner, deterministic exercise types, progress events, and transparent profile-driven starter paths.
3. Deliver the first coherent English and communication curriculum: grammar in context, sentence construction, vocabulary, speaking fluency, listening comprehension, and listen/repeat pronunciation practice.
4. Add learner-approved learning memory and revision cards, then a simple transparent local review scheduler.
5. Add project, HR/behavioural, and technical interview studios on shared scenario infrastructure.
6. Add evidence-based progress, goals, explainable recommendations, and local export/backup/restore.
7. Complete accessibility, privacy/security, responsive UX, fresh-install, target-device, and release acceptance checks.

Each phase must preserve the existing FastAPI + plain HTML/CSS/JavaScript + SQLite modular monolith, additive database migrations, versioned JSON content, zero mandatory operating cost, and usable text fallback. A feature is complete only after its end-to-end flow, tests, failure states, documentation, and manual acceptance are evidenced. Do not claim certified proficiency, accurate pronunciation grading, placement probability, or measured learning gains without separate validation.

## 16. Learning Engine — implemented slice and boundaries (2026-11-19)

The first Phase B implementation adds a reusable local lesson engine on the existing stack:

- A versioned JSON curriculum with 14 skills, one foundation level, six units, three goal-based tracks, six lessons, prerequisites, outcomes, examples, and deterministic choice, ordering, vocabulary, listening, short-response, and reflection exercises.
- A validator that rejects duplicate identifiers, broken references, unsupported exercise types, and malformed answer/token definitions.
- APIs for catalogue/recommendations, attempt creation and retrieval, ordered response submission, and progress.
- Additive SQLite learning-attempt and learning-event persistence, including restart-safe resume.
- Profile goal/focus-based recommendations with an explanation for each lesson.
- A browser learning workspace with route, catalogue, exercise runner, feedback, progress, and resume UI.

This slice does not automatically grade open responses, infer learner proficiency, or claim learning gains. A short low-stakes baseline check is implemented; it stores observable responses without assigning a level or score. Advanced diagnostic interpretation, broader English curriculum, personal revision memory, broader listening and pronunciation curriculum, and dedicated career/interview packs remain planned. Automated and target-device acceptance must be recorded before calling this phase complete.
