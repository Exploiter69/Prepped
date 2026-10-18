# Prepped — Complete Project Roadmap

**Status:** Working roadmap for the complete TDP, from research archive to evaluated prototype  
**Date:** 2026-10-19  
**Planning basis:** B.Tech semester 3 now; TDP continues through the final year. Dates are decision gates, not promises that every feature will be delivered.  
**Companion documents:** [Complete Product Blueprint](PRODUCT_BLUEPRINT.md) · [Research Decision Matrix](RESEARCH_DECISION_MATRIX.md)

## 1. The destination

Prepped is a practice environment for Indian engineering students preparing for placement interviews and other professional conversations. It should help a student practise a realistic conversation, receive specific feedback tied to what they actually said, retry, and learn from the difference.

The full project may eventually include voice, multiple scenarios, review scheduling, validated assessment, multilingual support, and institution-facing features. Those are not all first-release requirements. The project is successful only if the team can demonstrate a working core, explain the design, test it, collect real user evidence, and honestly report limitations.

### Product loop

1. Choose a scenario with a clear goal.
2. Answer a simulated interviewer.
3. Handle a few relevant follow-up questions.
4. Review a transcript or answer history.
5. Receive feedback tied to actual answer evidence.
6. Retry with the same checklist.
7. Compare the attempts and record what changed.

The first proof is this loop working end to end—not an avatar, a dashboard, or a large architecture diagram.

## 2. Current baseline and truth reset

As of 2026-10-19, the GitHub repository contains research reports, archive-verification notes, a README, and a product blueprint. The repository tree does not yet show an application implementation. Therefore:

- **Research collected:** yes, five AI reports archived.
- **Product direction selected:** yes, one text-first project-interview scenario.
- **Application implemented:** not yet evidenced in the repository.
- **User pilot run:** not yet evidenced.
- **Placement-readiness improvement measured:** no.
- **Voice pipeline benchmarked on target hardware:** no.
- **AI scoring validated against human raters:** no.

The old Phase 2 PPT/report proposed graph logic, voice, avatars, “Skill DNA,” institutional heatmaps, and an estimated 40% improvement. These are historical proposal claims, not proof of implementation or results. The roadmap replaces them with verifiable gates. Remove the 40% claim from future presentations unless an appropriate study supports it.

## 3. Hard constraints

- No mandatory paid APIs, subscriptions, hosted databases, paid hosting, or pay-per-use services.
- The core demo must work locally without an external model account.
- GitHub is the source of truth; decisions, code, tests, and evidence belong in the repository.
- Keep one application and one simple data store until evidence proves a need for more.
- Do not add Redis, Kafka, Celery, Kubernetes, microservices, a vector database, or a second workflow system for the MVP.
- Use the smallest end-to-end slice rather than implementing infrastructure layers before a working feature exists.
- Never claim that a planned feature exists; require code, a reproducible demo, and tests.
- Keep personal data minimal. Do not store raw audio by default.
- Never present generated feedback as a formal hiring decision or validated placement predictor.

## 4. Workstreams

| Workstream | Purpose | Starts | Can expand only when |
|---|---|---|---|
| Product and scenario design | Define user task, scenario, follow-ups, success conditions | Immediately | Pilot evidence identifies a new need |
| Core application | Build a local, usable end-to-end practice loop | Immediately | Core acceptance tests pass |
| Feedback and evaluation | Ground feedback in answer evidence and a transparent rubric | With first scenario | Human review shows acceptable quality |
| Privacy and safety | Minimize data, validate outputs, provide deletion | From first stored session | Public use requires further review |
| Voice feasibility | Test local STT, LLM, TTS, latency, and hardware | After text MVP and pilot | Measured usability justifies voice integration |
| Learning loop | Retry comparison, later review items and spaced repetition | Retry in MVP; review items later | Feedback/item quality is useful and repeatable |
| Academic evidence | Keep experiments, decisions, test results, and limitations | From day one | Every phase adds evidence |
| Institutional expansion | Cohorts, faculty views, LMS, multi-user administration | Final-year option only | A real stakeholder need and privacy basis exist |

## 5. Phase 0 — Reset, scope, and reproducibility

**Purpose:** establish one shared project truth before implementation.

### Tasks
- Keep the five source reports and verification notes unchanged.
- Review the research decision matrix and agree that it governs scope.
- Keep the product blueprint and this roadmap in GitHub.
- Create a clear distinction in project documents between proposed, implemented, tested, observed, and externally reported claims.
- Define the first scenario: explain a project to a placement interviewer.
- Define the initial rubric: clarity, structure, specificity, relevance to the follow-up, and conciseness.
- Agree on what the first demo must show and what it must not claim.

### Deliverables
- Product blueprint.
- Source-to-decision matrix.
- Complete roadmap.
- Scenario specification and feedback rubric.
- Initial acceptance checklist.

### Exit gate
The team can explain in plain language: who Prepped serves, which first problem it solves, what the first version does, what it does not do, and how success will be checked.

## 6. Phase 1 — First runnable local application

**Purpose:** make the smallest working software skeleton.

### Tasks
- Create a Python project with FastAPI.
- Serve a simple HTML/CSS/JavaScript interface from the same application.
- Add a health/status page and clear local run instructions.
- Use SQLite for local session records.
- Add versioned JSON for the first scenario and its rubric.
- Add basic automated tests and a clean setup path.
- Add a visible explanation when optional AI/model support is not configured.
- Do not require authentication for the first local-only demo unless there is a specific need.

### Deliverables
- Application starts locally with a documented command.
- First screen explains the scenario and lets the learner begin.
- Scenario and rubric are readable, versioned files.
- Tests run from a fresh checkout.

### Exit gate
A teammate can clone the repository, follow the README, run the app locally, and reach the first scenario without a paid service or undocumented setup.

## 7. Phase 2 — One complete text scenario

**Purpose:** prove the core learning loop end to end.

### Scenario
The learner explains a project to a simulated placement interviewer. The interviewer asks a small number of follow-ups about the problem, the learner's contribution, design choices, evidence/results, and lessons learned. Follow-ups should be relevant to what the learner has said; the first version may use deterministic rules and curated question branches.

### Tasks
- Implement session start, turn capture, and session completion.
- Implement a small deterministic scenario state controller.
- Keep the allowed states and transitions explicit and testable.
- Support empty answers, user cancellation, restart, and graceful completion.
- Show a transcript or ordered answer history.
- Provide evidence-linked feedback using the same rubric each time.
- Provide a retry action and side-by-side comparison of first and second attempts.
- Store session history locally and allow the learner to delete a session.
- Add optional local LLM support behind a narrow adapter only if it can be run without a paid API; retain deterministic fallback behaviour.
- Validate model output and never let model text directly modify state or database permissions.

### Minimum feedback format
- **What worked:** one or two observable strengths.
- **What needs work:** a specific issue linked to the answer.
- **Evidence:** quote or point to the learner's actual words.
- **Next action:** a concrete improvement to try.
- **Uncertainty:** “not enough evidence” when the answer does not support a conclusion.

### Tests
- Scenario starts and ends correctly.
- Each state has a reachable next state or a terminal condition.
- Follow-up branch is selected as expected for representative answers.
- Empty and very long answers are handled.
- Feedback evidence belongs to the actual learner answer.
- Invalid model output does not crash the app or invent a score.
- Retry uses the same scenario and rubric version.
- Deletion removes the selected local session data.

### Exit gate
A new user can complete the scenario, receive evidence-linked feedback, retry, compare attempts, and delete history. The full flow works locally with no paid API.

## 8. Phase 3 — Internal quality and small student pilot

**Purpose:** discover whether the actual product is understandable and useful.

### Pilot design
- Recruit 10–20 student volunteers if available and appropriate.
- Explain that this is a prototype, not a placement predictor.
- Ask each participant to complete the same scenario, review feedback, and retry.
- Do not require participants to provide confidential project or personal information.
- Collect only the minimum information needed; anonymize notes where practical.
- Do not record raw audio in the text MVP.

### Record
- Completion without help.
- Steps that caused confusion.
- Whether each feedback item points to something actually present in the answer.
- Whether the learner understands the next action.
- Differences between the first and second answer using the same checklist.
- Whether the learner would voluntarily practise again.
- Bugs, failure cases, and completion time.
- Sample size, method, and limitations.

### Exit gate
A short pilot report records what worked, what failed, the observed counts, and the next decision. A positive result is not mandatory. The gate passes when the evidence is documented and the team makes a reasoned decision to iterate, narrow, or proceed.

## 9. Phase 4 — Improve feedback and attempt comparison

**Purpose:** fix quality problems before adding new product surfaces.

### Tasks
- Review anonymized pilot examples.
- Create a small feedback test set containing strong answers, vague answers, unsupported claims, irrelevant answers, and insufficient-evidence cases.
- Check that feedback quotes the learner accurately and avoids invented details.
- Compare deterministic checklist feedback with optional local-model suggestions.
- Keep human-readable reasons for rubric criteria.
- Add rubric/scenario version identifiers to saved sessions.
- Improve retry comparison without collapsing the learner into a single overall number.

### Exit gate
The test set passes the agreed grounding checks, known failure cases are documented, and feedback is understandable to a student reviewer. If the model cannot meet the bar, keep the deterministic checklist rather than hiding the failure.

## 10. Phase 5 — Local voice feasibility spike

**Purpose:** determine whether voice is technically feasible on the actual available hardware and still compatible with zero mandatory spend.

This is a research spike, not permission to rewrite the app around a voice framework.

### Compare
- Local STT candidates such as faster-whisper or whisper.cpp.
- A local TTS candidate such as Piper or Kokoro.
- A locally runnable LLM through the same narrow adapter, if hardware supports it.
- A simple push-to-talk or record-and-submit flow before attempting full-duplex live audio.

### Measure
- Hardware and model versions.
- Cold start and warm response time.
- Transcription errors on representative student speech, with consent.
- Memory and CPU/GPU use.
- Failure rates and setup burden.
- Whether the voice path remains usable on the actual laptop.
- What works without GPU and what does not.
- Whether text/captions remain a usable fallback.

### Rules
- Do not copy latency figures from AI reports as if they were measured on our hardware.
- Do not rely on temporary free API credits.
- Do not integrate avatars, lip-sync, or streaming orchestration during this spike.
- Do not store raw audio by default.
- If local voice is too slow or difficult, retain text mode and document the result.

### Exit gate
A reproducible benchmark and a written go/no-go decision exist. Voice proceeds only if the measured experience is useful, maintainable, and compatible with the project constraints.

## 11. Phase 6 — Voice practice, only if the gate passes

**Purpose:** add voice without losing evidence, control, accessibility, or zero-cost operation.

### Tasks
- Add microphone permission flow and visible recording state.
- Start with push-to-talk or short recorded turns.
- Show editable/inspectable transcript text before using it for feedback.
- Add captions for spoken output and text alternatives.
- Keep the deterministic scenario controller as the authority.
- Add timeouts, cancellation, retry, and a visible failure message.
- Benchmark latency and transcription quality on real student devices and networks.
- Add streaming and interruption handling only if the simpler voice interaction proves useful.
- Choose LiveKit Agents or Pipecat only after a small comparison using the same scenario and measured criteria.

### Exit gate
The scenario completes through voice on the target hardware, transcript errors can be corrected or acknowledged, captions/text fallback works, and tests cover permission denial, STT failure, model failure, and session cancellation.

## 12. Phase 7 — Conversation-to-review loop

**Purpose:** test whether session mistakes can become useful repeated practice.

### Tasks
- Start with a small set of candidate review-item types: missing project detail, unsupported claim, unclear explanation, and a useful response structure.
- Link every candidate item to the source answer and explain why it was suggested.
- Let the learner accept, edit, or reject a candidate.
- Deduplicate near-identical items.
- Track whether the learner actually uses the item in a later attempt.
- Only after item quality is acceptable, compare a simple schedule with an FSRS implementation.
- Keep review history and deletion behaviour testable.

### Exit gate
Review items are accurate, useful, non-duplicative, linked to evidence, and reused in a later scenario. If AI-generated items are noisy, keep a manual or rules-based review list instead.

## 13. Phase 8 — Second scenario and reusable scenario format

**Purpose:** prove that the scenario format can support more than one use case without becoming a generic platform.

Candidate second scenarios:
- Explain a technical concept to a non-technical interviewer.
- Handle a follow-up question about a design decision.
- Explain a project setback and what was learned.

Choose based on pilot feedback, not novelty.

### Tasks
- Define a shared scenario schema.
- Add validation for required fields and valid transitions.
- Separate interviewer persona instructions from feedback rubric instructions.
- Test that every state is reachable and terminal states are possible.
- Ensure model responses cannot reveal hidden scenario facts or skip required transitions.
- Add one new scenario and compare whether existing code can support it with little special casing.

### Exit gate
Two scenarios use the same session and feedback infrastructure; scenario-specific logic remains in data where appropriate; tests prevent dead states and unintended transitions.

## 14. Phase 9 — Human-calibrated assessment research

**Purpose:** establish whether any rubric-based outputs are consistent enough to be presented as more than formative guidance.

### Tasks
- Define each rubric criterion in observable language.
- Recruit human reviewers where possible and document their background and instructions.
- Compare AI suggestions with human ratings on the same anonymized responses.
- Measure disagreements and recurring failure types.
- Test repeatability across repeated runs and prompt/model versions.
- Keep human judgements and model outputs distinguishable.
- Do not introduce an overall “communication score” until there is evidence and a clear explanation of its limits.

### Exit gate
A written calibration report shows sample size, rubric, agreement method, examples of disagreement, and limitations. If results are weak, keep the product at checklist feedback.

## 15. Phase 10 — Final-year options, not automatic commitments

Only consider these after the core loop, pilot, and evidence are solid:

- More scenarios for interviews, presentations, teamwork, negotiation, or difficult conversations.
- Shadowing and playback-speed controls.
- Pronunciation or prosody feedback if local audio models and human validation justify it.
- Multilingual interface or practice languages based on user need and tested quality.
- Instructor assignment or review tools if a faculty member requests them and learner privacy can be protected.
- Export of sessions or review items.
- Institution accounts, cohort analytics, SSO, LMS integrations, multi-tenant cloud hosting, mobile packaging, avatars, VR, and marketplace features.

Every new capability requires a problem statement, zero-cost plan, acceptance criteria, privacy assessment, and a reason it is more important than improving the existing learning loop.

## 16. Semester-by-semester TDP map

These are intended outcomes for a four-year programme where semester 3 is the current point. Actual dates should be adjusted with the guide and team schedule.

| Semester | Primary objective | Expected evidence / deliverable |
|---|---|---|
| **Semester 3 — reset and first working slice** | Finalize scope; build local text scenario; grounded feedback and retry | Runnable local demo, tests, updated README, scenario/rubric, architecture note |
| **Semester 4 — usability and first pilot** | Test with students, fix feedback and interaction issues, benchmark local model options | Pilot report, issue log, feedback grounding test set, decision log |
| **Semester 5 — voice feasibility and optional voice MVP** | Measure local STT/LLM/TTS; integrate voice only if the gate passes | Reproducible benchmark, go/no-go note, voice demo or documented text-first decision |
| **Semester 6 — learning loop and second scenario** | Improve attempt comparison; validate review-item quality; add a second scenario if useful | Review-loop tests, scenario schema, two-scenario demo, user findings |
| **Semester 7 — assessment and robustness** | Human calibration, privacy/safety testing, accessibility, failure cases | Calibration report, threat/privacy review, accessibility checklist, regression tests |
| **Semester 8 — final integration and TDP evidence** | Stabilize, document, demonstrate, evaluate, and prepare final submission | Release candidate, reproducible demo instructions, final report, presentation, results/limitations, future-work plan |

A semester's outcome is evidence, not just a list of features. If a gate fails, the team should report the finding and keep the previous working version rather than adding features to make the roadmap look complete.

## 17. Testing strategy

### Every change
- Unit tests for scenario transitions and feedback structure.
- Regression tests for previously found bugs.
- Manual smoke test from a clean start.
- No secrets or personal data in Git.

### Before a demo
- Fresh clone and setup.
- Main scenario completes.
- Empty and unexpected inputs behave safely.
- Feedback evidence matches the answer.
- Retry uses the same rubric.
- Deletion works.
- Model absent or invalid output does not crash the application.
- Keyboard navigation and readable layout work.

### Before a student pilot
- Clear prototype disclaimer.
- Consent and minimal-data plan.
- No raw audio retention by default.
- Anonymous note-taking process.
- Known limitations documented.

### Before voice
- Permission denial, device unavailable, network failure, transcription correction, cancellation, timeout, and fallback tests.
- Stage-level timing measurements on the actual target machine.

### Before any formal score or institutional data
- Human-rater calibration.
- Privacy and security review.
- Access-control tests.
- Explicit evidence and limitation statement.

## 18. Team and faculty operating model

For every phase, keep five small artefacts:

1. **Decision log:** what was decided, why, alternatives rejected, and what evidence could change the decision.
2. **Implementation log:** links to commits and files, not just a claim that work is complete.
3. **Test record:** command run, outcome, environment, and known failures.
4. **Evidence log:** pilot method, sample size, anonymized observations, and limitations.
5. **Demo script:** steps that another teammate or faculty member can follow to reproduce the result.

Do not write future tense as past tense. A proposed architecture belongs in design documentation; a tested implementation belongs in implementation/evidence documentation.

## 19. Final completion criteria

Prepped is ready for final TDP submission when the team can provide:

- A working application that runs from documented instructions.
- A clear explanation of the user problem and why the first scenario was chosen.
- A traceable architecture and scenario definition.
- Tests for core behaviour, failure handling, and deletion.
- Evidence that feedback references actual learner answers.
- A pilot or other clearly described evaluation with sample size and limitations.
- A documented voice decision based on measurement, whether go or no-go.
- No unsupported placement-readiness or learning-improvement percentage.
- A final report distinguishing implemented features, tested properties, observed outcomes, hypotheses, and future work.
- A live demo that does not depend on a paid account or an expiring free API quota.

## 20. Immediate next actions

1. Create the application skeleton and local run instructions.
2. Add the first scenario JSON and rubric.
3. Implement the deterministic text session controller.
4. Build answer capture, feedback, retry, local history, and deletion.
5. Add tests for the full core loop.
6. Demonstrate it from a clean checkout before expanding scope.

**The immediate milestone is one complete local text scenario with evidence-linked feedback and retry. Voice and advanced features are gated by results, not assumed in advance.**
