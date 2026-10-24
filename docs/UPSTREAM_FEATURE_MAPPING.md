# Prepped — Upstream Feature-to-Blueprint Mapping

**Version:** 1.0  
**Date:** 2026-10-24  
**Status:** Decision document for Step 2. No upstream code is imported by this document.  
**Inputs:** [Product Blueprint](PRODUCT_BLUEPRINT.md), [Complete Roadmap](COMPLETE_ROADMAP.md), [Research Decision Matrix](RESEARCH_DECISION_MATRIX.md), and [Upstream Repository Audit](UPSTREAM_REPOSITORY_AUDIT.md).

## 1. Purpose and decision rules

This document translates the three upstream repositories into explicit decisions for Prepped. It is not a feature shopping list. Each candidate is judged against Prepped's first job: help an Indian engineering student practise explaining a project to a placement interviewer, receive evidence-linked feedback, retry with the same rubric, compare attempts, and delete local history.

### Hard constraints

1. The first complete product flow remains text-first.
2. The core application must work without external AI credentials, paid APIs, hosted services, or an inference-provider connection.
3. Keep one application, Python/FastAPI, plain HTML/CSS/JavaScript, SQLite, versioned JSON scenario definitions, and a deterministic Python session controller unless evidence shows a real blocker.
4. Do not introduce PostgreSQL, Redis, queues, microservices, a graph/workflow engine, a vector database, or separate deployable services to imitate an upstream repository.
5. Feedback must refer to the learner's actual words and support “not enough evidence.” It is formative guidance, not a hiring decision or validated score.
6. Keep session data local and minimal; no audio is stored in the text MVP; saved session data must be deletable.
7. Do not copy Sotto code under its current PolyForm Noncommercial license into a project that may later be commercialized without resolving the licensing issue.
8. No imported code is approved until the exact file, pinned source commit, license/notice, dependencies, changes, and tests have been reviewed.

### Decision labels

- **REUSE CODE (conditional):** a narrow code unit may be copied only after commit-pinned source and license review; preserve notices and test it within Prepped.
- **ADAPT THE PATTERN:** implement the same useful design in Prepped's existing stack; no source-code copy is implied.
- **BUILD OURSELVES:** product-specific logic should be authored and owned in Prepped.
- **DEFER:** potentially useful after the current milestone passes its acceptance gate.
- **REJECT FOR MVP:** adds cost, complexity, risk, or unsupported claims without helping prove the first learning loop.
- **REFERENCE ONLY:** study design concepts; no code import planned.

## 2. Source-to-decision overview

| Source | Strongest contribution | Decision for Prepped | Code reuse status |
|---|---|---|---|
| AI Mock Interviewer | Small interview lifecycle, SQLite-backed session/answer persistence, injected gateway, deterministic fallback and focused service tests | Primary code-level reference for selected small units; reimplement if Python adaptation is simpler than porting Node code | Conditional only; no code imported yet |
| DeepInterview | Prep/live/post boundaries, provider interfaces, typed contracts and mock-first pipeline | Adapt separation and adapter contracts inside one FastAPI application | Pattern reuse; no framework or service import |
| Sotto | Learning loop, mastery gates, learner notes, spaced repetition and adaptive review concepts | Reference only for later learning milestone; implement simple Prepped-specific review logic independently | No Sotto code reuse approved |
| Prepped blueprint | Product scope, rubric, privacy policy, local architecture and semester gates | Governing specification | Source of truth |

## 3. Feature mapping matrix

### A. First milestone — local text practice and feedback

| Candidate feature/pattern | Upstream evidence | Blueprint fit | Decision | Implementation boundary / reason |
|---|---|---|---|---|
| Session lifecycle: create, start, answer, advance, complete | AI Mock Interviewer service methods and tests | Direct fit for scenario start, bounded turns, finish and retry | **ADAPT THE PATTERN**; conditional code reuse after review | Implement a small Python session controller. Reuse a narrow algorithm only if it is cleaner than a faithful Python implementation; do not port the Node app. |
| Deterministic scenario state machine | DeepInterview staged pipelines; AI Mock Interviewer controlled flow | Direct fit for explicit states and allowed transitions | **BUILD OURSELVES** | Scenario and follow-up rules are Prepped-specific. Scenario JSON defines states; Python owns transition authority. No LLM may skip or invent states. |
| Versioned scenario definitions | Both interview tools use structured question/configuration concepts | Direct fit for reproducible sessions | **BUILD OURSELVES** | Create one versioned JSON scenario and validate its schema. Store scenario ID/version on every session so edits do not silently change old attempts. |
| Follow-ups based on the actual answer | DeepInterview adaptive-interview goal; AI Mock Interviewer question gateway | Direct fit, but must remain bounded and explainable | **ADAPT THE PATTERN** | Start with explicit answer signals and curated branches. Do not make a general-purpose autonomous interviewer. Model-generated wording is optional and must fit an allowed branch. |
| Provider/gateway interface | Both interview projects isolate question/AI generation behind interfaces | Direct fit for optional local AI and deterministic fallback | **ADAPT THE PATTERN** | Define a tiny Python interface for candidate follow-up phrasing or suggestions. The controller, storage and completion path never depend on it. Avoid a plugin framework. |
| Deterministic no-credentials path | AI Mock Interviewer's offline mode; DeepInterview mock adapters | Core blueprint requirement | **BUILD OURSELVES**, using the pattern | Built-in scenario and deterministic feedback must work with no model installed and no external key. “Mock mode” must not pretend it is real AI. |
| Transcript / ordered answers | AI Mock Interviewer session and answer persistence | Direct fit for review and feedback evidence | **ADAPT THE PATTERN** | Use minimal SQLite storage for turns/answers. Keep ordering explicit. No accounts, CVs, job-description uploads or profile data in the first MVP. |
| Feedback checklist | AI Mock Interviewer template feedback; DeepInterview post-session evaluation | Direct fit, but Prepped requires answer-grounded evidence and uncertainty | **BUILD OURSELVES** | Implement Prepped's five criteria: clarity, structure, specificity, follow-up handling and conciseness. Each item must cite real answer text or say “not enough evidence.” Do not import a generic scoring engine. |
| Feedback schema and validation | DeepInterview shared TypeScript/Pydantic contracts; both projects isolate provider output | Direct fit for reliable rendering | **ADAPT THE PATTERN** | Use a small Python schema/model. Reject malformed output, invalid evidence references, invented quotes, extra fields and unsupported numeric scores; then fall back deterministically. |
| Evidence references / quote grounding | Prepped's core principle; upstream evaluation concepts only partially match | Mandatory product differentiator | **BUILD OURSELVES** | Evidence must be a verbatim substring or stable span/reference to the learner's actual answer. Validate it. Generic praise without evidence does not count as grounded feedback. |
| Retry with same rubric | AI Mock Interviewer supports repeated practice; DeepInterview uses weak areas for future practice | Direct fit for core loop | **BUILD OURSELVES** | Start a new session with the same scenario and rubric versions. Never overwrite the original attempt. Make version differences visible. |
| Attempt comparison | AI Mock Interviewer saves progress; Prepped blueprint explicitly calls for same-rubric comparison | Mandatory first MVP feature | **BUILD OURSELVES** | Compare checklist criteria and answer excerpts side by side. Describe observable differences, not a calibrated score or proof of employability improvement. |
| Local session history and deletion | AI Mock Interviewer local SQLite persistence; Prepped requires explicit deletion | Direct fit | **ADAPT THE PATTERN** | Use SQLite foreign keys/transactions or explicit cascade deletion and tests. Delete session, turns and feedback together. No cloud sync or mandatory account. |
| Limits on answer length and turn count | AI Mock Interviewer validates interview limits; DeepInterview separates the live path | Direct fit for safety and predictable performance | **ADAPT THE PATTERN** | Choose explicit maximum answer length and turns; validate server-side. Handle empty answers and cancellation. Tune limits with tests. |
| Error handling / graceful completion | All three projects have provider/service failure paths | Direct fit | **ADAPT THE PATTERN** | Provider timeout or invalid output cannot lose an answer or strand a session. Text flow completes without optional AI. At most one bounded model retry. |
| Session/rubric provenance | DeepInterview typed contracts; Prepped requires versioned scenario/rubric | Direct fit | **BUILD OURSELVES** | Store scenario version, rubric version, feedback mode and model/prompt version only if used. Never store secrets. |
| Tests with fake provider and SQLite | AI Mock Interviewer service tests use fake gateway and in-memory SQLite | Direct fit | **ADAPT THE PATTERN** | Use pytest and temporary/in-memory SQLite with a fake provider. Tests must not call internet, require model downloads or API keys. |
| Full web framework/front-end stack | DeepInterview uses Next.js/React; Sotto uses Next.js/React | Not required | **REJECT FOR MVP** | Keep plain HTML/CSS/JS and FastAPI. Rewriting UI to match upstream adds no proof of learning value. |
| Account/authentication and hosted user store | AI Mock Interviewer hosted account/database paths; Sotto broader user system | Explicitly excluded from local MVP | **DEFER** | Revisit only if a real multi-user deployment need and privacy/security plan emerge. |
| CV/JD/company research ingestion | DeepInterview preparation workflow | Different from first scenario; adds data and external-service risk | **DEFER** | First scenario is the learner's own project explanation. Avoid CV collection or research-provider calls before a proven need. |
| Large question bank | AI Mock Interviewer broad question bank | Not needed to validate one scenario | **DEFER** | Write and test one coherent scenario first. Review provenance and licensing before importing question content. |
| Avatar, voice persona and animation | DeepInterview voice-first experience | Explicitly outside first MVP | **REJECT FOR MVP** | Does not prove grounded feedback; adds resource, accessibility and implementation burden. |
| Browser Speech Recognition | AI Mock Interviewer uses browser speech APIs | Conflicts with reliable offline/privacy expectation if assumed local | **DEFER / NOT DEFAULT** | Do not make browser speech the voice foundation. Test network behavior and privacy if considered later. |

### B. Second milestone — learning and review

| Candidate feature/pattern | Upstream evidence | Blueprint fit | Decision | Implementation boundary / reason |
|---|---|---|---|---|
| Review items tied to observed weaknesses | Sotto notes/review model; Prepped evidence-linked feedback | Fits after feedback is useful and consistent | **ADAPT THE PATTERN** | Generate a small review item from an actual rubric observation, such as “state your contribution and name one design decision.” Do not create generic flashcards from every answer. |
| Spaced repetition scheduling | Sotto learning design | Possible future benefit; not needed for first loop | **DEFER, then BUILD OURSELVES** | Start with a transparent schedule only after pilot evidence supports repeat review. Use local SQLite and simple date calculations, not Redis, a queue or a background service. |
| Mastery gates / prerequisite progression | Sotto mastery-gated course progression | Potentially useful in a larger curriculum but risks false precision | **DEFER** | Do not gate access to the first scenario. Later gates need human-reviewed criteria and evidence; avoid opaque mastery scores. |
| Adaptive review ordering | Sotto adaptive-learning ideas | Potentially useful when several validated review items exist | **DEFER** | First use inspectable ordering: due date, user choice, or repeated observed weakness. Avoid a model-driven “skill graph” before evidence exists. |
| Vocabulary memory graph / knowledge graph | Sotto | Not aligned to the first task; adds complexity | **REJECT FOR MVP** | No graph DB, embeddings or knowledge graph. A simple review-item table is enough initially. |
| Course/CEFR progression | Sotto language-learning domain | Prepped is professional conversation practice, not a CEFR course | **REJECT FOR MVP** | Do not transplant CEFR or language-course assumptions into interview feedback. |
| Notes and learner reflection | Sotto learner-note concept | May support retry review but not core to first slice | **DEFER** | If pilot users request it, add a small optional local note attached to an attempt/review item, with deletion. Do not infer personal traits. |
| Multi-skill curriculum / many scenarios | Sotto and interview project catalogs | Longer-term expansion only | **DEFER** | Add a second scenario only after the first scenario's completion, feedback and retry loop has been tested with learners. |
| Background jobs / Redis / BullMQ | Sotto infrastructure | No need for current single-user local flow | **REJECT FOR MVP** | Review scheduling can be computed when the app opens. No daemon, queue or second workflow system. |

### C. Third milestone — voice feasibility and later integration

| Candidate feature/pattern | Upstream evidence | Blueprint fit | Decision | Implementation boundary / reason |
|---|---|---|---|---|
| Prep/live/post separation | DeepInterview | Useful if voice makes session phases more complex | **ADAPT THE PATTERN** | Keep logical stages in the same application. Do not create separate deployable services. |
| Local speech-to-text | DeepInterview and Sotto local profiles use faster-whisper or related local inference; AI Mock Interviewer uses browser speech | Fits later voice gate if measured on target hardware | **DEFER** | Benchmark one local STT option on the actual laptop. Record model/download size, peak RAM/CPU, latency, transcription quality and network behavior. |
| Local text-to-speech | DeepInterview/Sotto local profiles include local TTS options | Useful after STT is viable | **DEFER** | Evaluate one option after STT and text interaction work. Do not install a full voice stack in the first MVP. |
| Real-time duplex voice / streaming orchestration | DeepInterview LiveKit pipeline and Sotto service architecture | More complex than first practice requirement | **DEFER** | First voice version can be turn-based: capture one response, transcribe, allow correction, then reply. Streaming/interruption needs separate evidence. |
| Transcript correction and text fallback | Prepped blueprint explicitly requires transcript/caption and text alternative | Mandatory for any voice milestone | **BUILD OURSELVES** | Learner can correct transcription before it becomes feedback evidence. Mic denial, poor transcription, model absence and latency cannot block text practice. |
| Raw audio storage | Voice systems may process audio; Prepped excludes automatic raw-audio retention | Conflicts with privacy defaults | **REJECT BY DEFAULT** | Process locally and discard audio after the turn unless a later explicit consent-based feature is justified. |
| Cloud STT/TTS/LLM as required runtime | Hosted providers in voice stacks | Violates mandatory zero-cost constraint | **REJECT** | No API key or external account can be required. Optional external integrations require clear opt-in and cannot be the only path. |
| Voice performance assumptions from README | Upstream local profiles | No verified benchmark on target laptop | **REJECT AS EVIDENCE** | Do not claim usable offline voice until measured with reproducible setup on target hardware. |

## 4. Architecture mapping: what changes and what does not

### Keep unchanged

- Python + FastAPI as the single application/backend.
- Plain HTML, CSS and JavaScript frontend.
- SQLite as the one local data store.
- Versioned JSON for scenario and rubric definitions.
- Deterministic Python controller as authority for state and transitions.
- Deterministic feedback as guaranteed fallback.
- Optional local-model adapter only when configured.
- pytest or Python standard testing tools.
- GitHub as source of truth.

### Add only as small internal modules when implementation needs them

1. **Session service/controller:** lifecycle and allowed state transitions.
2. **Scenario loader/validator:** versioned JSON validation.
3. **Feedback schema/validator:** evidence references and allowed output structure.
4. **Provider interface:** optional suggestion generator; deterministic implementation always available.
5. **Attempt comparison function:** same rubric version, criterion-by-criterion comparison.
6. **Review-item module (later):** due dates and simple review state after the learning milestone is approved.

These are modules inside the same application, not services or a new workflow system.

### Explicitly do not add based on upstream examples

- Next.js/React rewrite.
- LangGraph or a general multi-agent graph.
- LiveKit and streaming voice workers in the text MVP.
- Supabase, S3/R2, PostgreSQL, Redis, BullMQ or hosted/queued infrastructure.
- LightRAG, vector search or knowledge graph.
- CV/JD ingestion, company web research or mandatory authentication.
- Avatar, animation, emotion inference or global communication score.
- A large imported question bank before content provenance and first-scenario quality are established.

## 5. File-level reuse policy

This mapping approves patterns and priorities, not automatic copying.

### First candidate to inspect further: AI Mock Interviewer

It is the first source to examine for a narrowly reusable lifecycle or test pattern because its repository license is MIT and its service design uses a fake gateway plus SQLite tests. Even then, prefer reimplementing the idea in Python if copying Node code would introduce a second runtime or make Prepped harder to maintain.

Before any copy, record:
- source repository and immutable commit SHA;
- exact file path and relevant line range;
- applicable license and copyright/notice requirements;
- any file-specific or dataset-specific license;
- changes made and why;
- any added dependency and its license;
- Prepped test proving behavior;
- attribution location in a THIRD_PARTY_NOTICES.md file if copying is approved.

### DeepInterview

Treat its contracts, adapter boundaries and prep/live/post structure as architectural inspiration. Copying a whole TypeScript/Python contract or framework module is not justified until a concrete duplication problem exists. Apache-2.0 notice and attribution obligations must be respected.

### Sotto

Do not copy application code, schema, service code, prompts, assets or datasets under the current root license without explicit license review. The safe current choice is to independently implement general learning ideas—such as due-date review—inside Prepped's existing SQLite design.

## 6. Acceptance criteria created by this mapping

The first text implementation is ready to progress only when all relevant items pass.

### Session and scenario
- [ ] A fresh checkout starts locally without cloud credentials.
- [ ] The first curated project-explanation scenario loads from versioned JSON.
- [ ] The controller allows only defined transitions and a bounded number of turns.
- [ ] Empty, cancelled, repeated and oversized answers have deliberate behavior.
- [ ] A session can complete without an optional model installed or running.

### Feedback
- [ ] Each feedback item uses the approved rubric and versioned schema.
- [ ] Evidence is an exact substring/span of the learner's answer, or the item explicitly says evidence is insufficient.
- [ ] Fabricated quotes, unsupported numeric scores and malformed model output are rejected.
- [ ] Provider failure returns deterministic feedback or a clear limitation message.
- [ ] No personality, emotion, intelligence, employability or placement-probability inference is produced.

### Retry and comparison
- [ ] Retry creates a separate attempt and preserves the original.
- [ ] Scenario and rubric versions are stored for each attempt.
- [ ] Comparison uses the same rubric version and describes observable changes.
- [ ] A version mismatch is flagged rather than presented as an apples-to-apples comparison.

### Persistence and privacy
- [ ] Session history is local.
- [ ] Deleting a session removes associated turns and feedback.
- [ ] Tests verify deletion after closing/reopening the database.
- [ ] No raw audio exists in the text MVP.
- [ ] No transcript is sent to a remote provider by default.
- [ ] Logs do not silently duplicate full learner answers without an explicit reason.

### Test independence and zero-cost
- [ ] Core tests run without internet, cloud keys, model downloads or external accounts.
- [ ] Fake-provider tests cover success, timeout/error and malformed output.
- [ ] At least one test runs with provider configuration absent.
- [ ] A clean-install smoke test and a separately documented no-network runtime test are recorded.
- [ ] Any optional local model is documented as optional and benchmarked separately from deterministic functionality.

These criteria should become tests/checklists as code is implemented. This document does not claim that they currently pass.

## 7. Deferred decision gates

### Gate A — complete text loop
Proceed only after the local scenario, grounded feedback, retry/comparison, deletion and deterministic no-key path work and have tests.

### Gate B — student pilot
Observe roughly 10–20 student volunteers if feasible. Ask whether feedback is specific, fair and useful; inspect cases where the system claims evidence that is absent. Do not optimize for an invented global score.

### Gate C — learning/review
Add review items only if pilot evidence shows a repeated weakness that students benefit from revisiting. Begin with explicit, locally stored items and a transparent due-date rule. Add spaced repetition only if it helps more than a simple retry/history view.

### Gate D — voice feasibility
Benchmark local STT first, then local TTS. Measure on the actual target laptop: model/download size, peak RAM, CPU use, turn latency, transcription correction rate and failure behavior. Voice integration is approved only if it remains usable and text fallback remains complete.

## 8. Final decision

**Build Prepped's own product-specific core. Borrow small engineering patterns selectively. Do not merge the three upstream apps.**

- AI Mock Interviewer: primary code-level reference, conditional and file-specific.
- DeepInterview: architectural patterns only for now.
- Sotto: later learning-design reference; no code import approved.
- Existing Prepped blueprint and constraints: authoritative.
- Next work after this mapping: Step 3, a minimal architecture delta decision. It should confirm that the current stack stays and list only the small modules/contracts needed for implementation. No code migration is warranted by this mapping alone.
