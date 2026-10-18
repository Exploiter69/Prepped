# Prepped — Research Review and Decision Matrix

**Status:** Research synthesis and product decisions  
**Date:** 2026-10-19  
**Purpose:** Preserve what the five AI reports recommend, show how their proposals were evaluated, and make the final decisions traceable.  
**Companion documents:** [Complete Product Blueprint](PRODUCT_BLUEPRINT.md) · [Complete Roadmap](COMPLETE_ROADMAP.md)

## 1. How to interpret this document

The five reports are research inputs, not five votes. Agreement between reports raises a question's priority; it does not prove a technical claim, market gap, legal interpretation, or learning outcome. Product decisions below are based on the reports, the project's zero-mandatory-spend constraint, the student team's scope, and the need to demonstrate working software and honest evidence.

Decision labels:

- **ADOPT NOW:** belongs in the first working vertical slice.
- **ADOPT LATER:** valuable, but only after the earlier stage works and a specific gate is passed.
- **EXPERIMENT:** plausible, but requires a measured test before commitment.
- **DEFER:** not required to prove the product's core value.
- **REJECT FOR THIS PROJECT:** conflicts with scope, evidence standards, privacy, or the no-mandatory-spend rule. This does not mean the idea is universally bad.
- **RE-VERIFY:** depends on fast-changing vendor, model, licence, pricing, or legal information.

## 2. Source integrity and review limits

The repository preserves the five supplied reports under research/raw/originals/ and the readable archives under research/raw/.

| Source | Preserved original | Fidelity status |
|---|---|---|
| Claude | Markdown source | Exact byte match to supplied source |
| Gemini Deep Research | Markdown source | Exact byte match to supplied source |
| DeepSeek | Text source | Exact byte match to supplied source |
| Perplexity | PDF source | Original PDF retained; extracted Markdown is a comparison/transcription, not byte-identical |
| Grok | PDF source | Original PDF retained; image-based pages make OCR imperfect, especially for tables |

The Perplexity PDF extraction has strong section and vocabulary correspondence with the archived Markdown, but that does not prove every sentence is identical. Grok's PDF-derived OCR covers the main report sections, but exact table wording cannot be certified from OCR. The original PDFs remain authoritative. Do not describe the two PDF-derived archives as word-for-word verified.

The original TDP Phase 2 PPT/report is also relevant context. It describes a directed-graph conversation engine, voice, avatar animation, rewind/retry, “Skill DNA,” institutional heatmaps, and an estimated 40% readiness improvement. Those are statements in the old academic artefact, not proof that those features were implemented or that the 40% outcome was measured. The new plan explicitly separates prior proposal, implemented work, and evidence.

## 3. Cross-report findings

| Finding | Reports contributing | Final decision | Why |
|---|---|---|---|
| Practice should be scenario-based, not just open-ended chat | All five, most explicitly Grok, Gemini, Perplexity, Claude | Adopt now | A bounded scenario is buildable, testable, and easy to explain to faculty |
| Feedback must point to actual learner evidence | Claude, Gemini, DeepSeek, Grok, Perplexity | Adopt now | Core trust requirement; feedback must quote or reference real answer text |
| Repeat practice is more valuable than one-off chat | Gemini, Grok, Perplexity; Claude/DeepSeek support session evidence and review loops | Adopt now | The first MVP includes retry against the same checklist |
| Voice is an important future differentiator | Gemini, DeepSeek, Grok, Perplexity, Claude | Adopt later through a feasibility gate | Voice creates STT/TTS, latency, device, accessibility, and hardware risks; first prove the learning loop |
| Use structured scenario state and explicit transitions | Claude, Gemini, DeepSeek, Grok, Perplexity | Adopt now in a minimal form | A small deterministic controller is enough; a general graph platform is not |
| Keep model providers replaceable | Claude, Gemini, DeepSeek, Perplexity | Adopt as a small interface | Prevents code coupling without building a general model gateway prematurely |
| Reuse learner mistakes in later practice | Gemini, DeepSeek, Grok, Perplexity, Claude | Adopt later | First validate feedback and retry; then test review-item quality before adding scheduling |
| FSRS is a strong candidate for review scheduling | Claude, Gemini, Perplexity | Experiment later | The algorithm is not the first product risk; review content quality and usefulness come first |
| Pronunciation / phoneme scoring can differentiate the product | Gemini, DeepSeek, Grok, Perplexity | Experiment later | Needs real audio, validated models, representative learner speech, and human comparison |
| Human ratings are needed to validate AI assessment | All five, especially Claude, DeepSeek, Perplexity | Adopt as an evaluation principle | Do not call AI scores objective or validated without calibration |
| Avatar, lip-sync, VR, and animated environments | Gemini, Grok, Perplexity; old TDP PPT | Defer | High effort and cost; no evidence they are necessary for the first learning loop |
| Institutional dashboards and multi-tenant deployment | Claude, Gemini, Grok, Perplexity; old TDP PPT | Defer | No demonstrated student value or institutional requirements yet |
| Complex production architecture is needed from day one | Claude, Gemini, Perplexity | Reject for the MVP | These designs target scale and real-time production, not a zero-budget student prototype |
| Mandatory managed voice/LLM APIs are acceptable because free credits exist | Gemini, DeepSeek, Perplexity | Reject as a dependency | Free credits and quotas can expire or change; the app must have a zero-cost baseline |
| “40% improvement in placement readiness” | Old TDP PPT/report, not established by the AI research | Reject unless a suitable study proves it | No baseline, sample, instrument, method, or result is documented |
| Emotion, confidence, or personality can be inferred from voice/tone and treated as a skill measure | Old TDP proposal and some feature suggestions | Reject for the MVP | High risk of misleading judgments; focus on observable answer content and task behaviour |

## 4. Claude — architecture and reliability report

**Report emphasis:** module boundaries, session lifecycle, event contracts, database, APIs, privacy, recovery, testing, hosting, and staged architecture.

### Adopted from Claude

- Separate observable evidence from judgement. Every feedback point should point to a turn or an answer excerpt.
- Keep scenario definitions versioned and validate their structure.
- Let deterministic application code own session state and transitions. An LLM may suggest a response or structured intent; it must not directly authorize actions or mutate state.
- Record the rubric and prompt/model version used to generate feedback so results can be reproduced as far as practical.
- Design for deletion, explicit consent, safe defaults, invalid model output, provider failure, and prompt injection.
- Use tests for scenario transitions, invalid output, duplicate actions, deletion, and recovery.
- Use a modular monolith rather than splitting every domain into services.

### Simplified rather than adopted wholesale

Claude's full proposal uses PostgreSQL, multiple domain schemas, realtime workers, event sourcing, a transactional outbox, durable jobs, room tokens, worker leases, object storage, row-level security, a model gateway, and possible Temporal migration. These are coherent production patterns, but most are unnecessary for a local first MVP.

For Prepped v1: one Python application, SQLite, JSON scenario files, a small deterministic session controller, simple session records, and a narrow optional model adapter. Introduce a background job or separate service only when a measured requirement demands it.

### Deferred from Claude

- Tenant IDs, institutional RBAC, instructor access, event-sourced aggregates, durable workflow engines, realtime worker leases, multi-provider failover, large observability stack, media storage pipeline, and enterprise SSO.
- Full assessment calibration infrastructure is deferred as implementation complexity, but the evidence and provenance principles remain mandatory now.

### Open questions from Claude retained

- What is the right rubric and what constitutes agreement with human ratings?
- What local voice stack works on actual hardware?
- Is an offline review queue needed?
- Which privacy/legal requirements apply to the pilot?
- Which licences and model versions are current at the time of selection?

## 5. Gemini Deep Research — product, learning, and technology report

**Report emphasis:** voice-first roleplay, shadowing, FSRS, pronunciation scoring, IELTS/ACTFL rubrics, avatars, institutional deployment, and a four-phase voice-led implementation plan.

### Adopted

- Practice should be active: learners produce an answer rather than only consume content.
- Use explicit scenario goals and follow-up questions.
- Feedback should be formative, specific, and tied to evidence.
- Repeat practice and review can help turn session mistakes into future learning, but this must be tested.
- Captions, text alternatives, adjustable playback, keyboard access, and clear microphone states belong in the product design.
- A local speech pipeline is worth testing after a text prototype works.

### Deferred

- Shadowing at a 150 ms delay, FSRS, GOP/CTC phoneme heatmaps, IELTS/ACTFL alignment, animated avatars, institutional dashboards, and multilingual roleplay.
- These features require more than adding a library: they require suitable audio, calibration, accessible UX, and evidence that the feature helps the target learner.

### Not accepted as guaranteed facts

Gemini's exact latency numbers, GPU requirements, model rankings, free-tier allowances, pricing, claims about FSRS review reduction, and legal statements must be independently rechecked before they appear in a proposal or public claim. Several numbers depend on hardware, measurement method, provider quota, or secondary sources. The reported 500 ms / 600 ms targets are hypotheses to benchmark, not MVP promises.

The report recommends Next.js/React, XState, LiveKit, Groq, Kokoro, PostgreSQL/Supabase, and a CTC GOP pipeline. That stack is not selected for Prepped v1: the current goal is a simpler local app that the team can build, explain, test, and run without required paid services.

## 6. DeepSeek — voice and AI pipeline report

**Report emphasis:** cascaded STT → LLM → TTS versus speech-to-speech, streaming overlap, VAD, interruption, model shortlist, local inference, reliability, latency, and cost.

### Adopted for the future voice gate

- Preserve a controlled/cascaded option where transcript, scenario state, and feedback evidence are inspectable.
- Treat audio models and orchestration as replaceable components.
- Measure latency by stage and report P50/P95/P99 rather than only averages.
- Test transcription on actual learner speech; general benchmarks do not establish performance on Indian English or a learner's accent.
- Make interruption cancellation, text/caption fallback, bounded timeouts, and visible failure behaviour explicit.
- Validate tool calls and model output; never allow the model to invent a score or act directly on a database.
- Run the feedback/evaluation path off the real-time response path if voice is added.

### Deferred

- Pipecat or LiveKit Agents selection, streaming STT, semantic turn detection, S2S fast path, multi-provider routing, model servers such as vLLM, and concurrency/load testing. These are voice-stage decisions, not prerequisites for text MVP.
- A sub-500 ms P95 target is not a promise. The report itself notes that targets depend on scenario class, hardware, network, and streaming overlap.

### Re-verify before use

The report contains many vendor prices, quotas, model latency/accuracy claims, licences, and hardware benchmarks from third-party and vendor sources. They are dated and configuration-dependent. Do not use them as current guaranteed values. The project remains zero-mandatory-spend; managed free tiers may be optional experiments, never a required runtime dependency.

## 7. Grok — competitor and opportunity report

**Report emphasis:** market landscape, product comparisons, underserved needs, differentiation, broad feature opportunities, and experiments.

### Adopted

- Position the product around a real practice task, not “another AI tutor.”
- Treat conversation-derived feedback and reuse as a possible differentiator.
- Include scenario branching and transfer between related practice tasks only when the core scenario works.
- Prioritise accessibility, low-bandwidth/text alternatives, and privacy.
- Treat competitors' claims and review summaries as hypotheses to verify, not evidence of Prepped demand or learning impact.
- Evaluate whether users find feedback specific, realistic, and worth repeating.

### Deferred

- A unified platform for language fluency plus every professional/soft skill, multi-agent simulations, calendar/job-description import, collaborative rooms, avatar environments, institution tooling, and a marketplace.
- These are possible later directions, not the first product promise.

### Fidelity and evidence caveat

The preserved Grok original is an image-based PDF. The readable Markdown and OCR comparison cover the report's main themes, but exact table-cell and wording fidelity cannot be certified from OCR. Competitor prices, feature comparisons, rankings, and claims about market gaps need fresh verification before external use.

## 8. Perplexity — broad product and roadmap dossier

**Report emphasis:** voice-first product vision, learner segments, competitor matrix, complete practice-feedback-review loop, architecture, data model, privacy, accessibility, assessment, costs, and a staged roadmap.

### Adopted

- The closed learning loop: scenario → answer → evidence-linked feedback → retry, with review items as a later extension.
- Scenario definitions should include roles, goals, states, follow-ups, and exit conditions.
- Assessment needs construct definitions, behavioral rubrics, human anchoring, reliability checks, and transparent uncertainty.
- Provide transcript/captions, replay and deletion controls, accessible alternatives, and a clear AI disclosure.
- Maintain separate test sets for normal behaviour, invalid/adversarial inputs, regression, and human-rated calibration.
- Treat free-tier capacity and per-session cost as constraints rather than assuming unlimited free usage.

### Narrowed

Perplexity recommends an initial 10-scenario voice MVP with authentication, review cards, FSRS, progress dashboard, replay, and provider abstraction. Prepped starts smaller: one project-explanation interview scenario, text-first, same-rubric retry, local history/deletion, and grounded feedback. The smaller wedge reduces the number of unknowns and lets the team collect meaningful pilot evidence before expanding.

### Rejected for the MVP

- Redis/Celery or other queues, vector databases, PostgreSQL, object storage, multi-provider voice orchestration, and mobile application stacks.
- These may be sensible in a later service with real deployment needs, but are not required for a local-first prototype.

### Re-verify

Competitor prices and feature claims, EU AI Act timelines, provider prices, and all claims about effectiveness or cost must be checked against current primary sources before formal use. Legal sections are a checklist for qualified review, not legal advice.

## 9. Original TDP proposal — retain the motivation, reset the claims

The prior Phase 2 materials call Prepped a “Social Flight Simulator” and propose:

- Directed-graph dialogue, a stress variable, adversarial personas, voice/STT/TTS, reactive avatars, rewind/retry, “Skill DNA” radar charts, and institutional heatmaps.
- Five proposed axes: empathy, negotiation, fluency, structural logic, and confidence.
- An estimated “40% improvement in readiness” and future predictive placement modelling.

Disposition:

- **Keep the underlying need:** students need a safe way to rehearse difficult professional conversations before real interviews or workplace interactions.
- **Simplify the graph:** use a small explicit state/turn controller for one scenario. Do not build a general-purpose graph platform.
- **Keep retry:** implement a learner-controlled retry and compare answers using the same rubric.
- **Replace Skill DNA for now:** use a transparent checklist with observable criteria. Do not claim to measure confidence, empathy, personality, or employability from a single AI session.
- **Defer avatar and institutional heatmaps:** no need to prove the learning loop.
- **Remove the 40% claim from new presentations and reports** unless a properly designed study produces that result. Label old text as a prior proposal, not a measured result.
- **Do not claim that Phase 2 features are implemented** unless there is code, a runnable demonstration, tests, and evidence for each feature.

## 10. Final product decisions

| Area | Decision for Prepped |
|---|---|
| Primary user | Indian engineering students preparing for placement/internship interviews |
| First scenario | Explain a project to a placement interviewer and handle a few relevant follow-ups |
| Initial interface | Local web app, text-first |
| Core loop | Scenario → answer → evidence-linked feedback → retry with same rubric |
| Backend | Python + FastAPI, one application |
| Frontend | Plain HTML/CSS/JavaScript initially |
| Storage | SQLite for local session history |
| Scenario authoring | Versioned JSON files |
| Dialogue state | Small deterministic controller |
| AI use | Optional local-model adapter; app remains demonstrable without a paid API or configured model |
| Feedback | Transparent checklist and concrete suggestions grounded in answer text |
| Voice | Gated feasibility milestone after text MVP and pilot |
| Review scheduling | Explore only after review-item quality is demonstrated; FSRS is a candidate, not a requirement |
| Scoring | No overall communication score in v1; no placement prediction |
| Privacy | Local-first, explicit saving/deletion, no raw audio storage by default |
| Infrastructure | No required hosted database, paid API, paid deployment, Redis, queue, microservices, Kubernetes, or vector store |
| Evidence | Tests, actual demo, pilot notes, human review, measured results; never substitute AI report recommendations for implementation evidence |

## 11. Evidence and claim rules for future documents

Every statement in a demo, poster, presentation, report, README, or website must fit one of these categories:

1. **Implemented:** exists in code and can be demonstrated.
2. **Tested:** an automated or repeatable test verifies the behaviour; name the test and its limits.
3. **Observed:** a pilot or experiment produced recorded results; include sample size and method.
4. **Proposed:** planned but not implemented.
5. **Hypothesis:** plausible, not yet established.
6. **Externally reported:** supported by a source; check source quality and date.

Do not convert “AI research says it is possible” into “Prepped does it.” Do not convert “a user liked it” into “it improves placement outcomes.” Do not report a percentage without a denominator, method, and source.

## 12. Source files

- Claude: [original report](../research/raw/originals/claude.md)
- Gemini Deep Research: [original report](../research/raw/originals/gemini-deep-research.md)
- DeepSeek: [original report](../research/raw/originals/deepseek.txt)
- Grok: [original PDF](../research/raw/originals/grok_report.pdf) · [readable archive](../research/raw/grok.md) · [PDF conversion comparison](../research/raw/converted/grok-from-pdf.md)
- Perplexity: [original PDF](../research/raw/originals/perplexity_report.pdf) · [readable archive](../research/raw/perplexity.md) · [PDF conversion comparison](../research/raw/converted/perplexity-from-pdf.md)
- Archive fidelity notes: [VERIFICATION.md](../research/raw/VERIFICATION.md)
