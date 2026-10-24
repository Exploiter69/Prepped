# ADR-001: Minimal local-first application architecture

**Status:** Accepted for the first MVP  
**Date:** 2026-10-24  
**Decision owners:** Prepped project team  
**Scope:** First runnable local application and one complete text-based project-interview scenario  
**Supersedes:** None

## Context

Prepped's approved product direction is a private, repeatable practice environment for Indian engineering students. The first job is to practise explaining a project to a placement interviewer, receive feedback tied to the learner's actual answer, retry against the same checklist, compare attempts, and delete saved local history.

The repository currently establishes the product direction and roadmap; this ADR is an implementation decision, not evidence that the application already exists. The upstream audit and feature mapping are inputs, not instructions to transplant another application's stack.

The architecture must support a useful, testable end-to-end slice with ₹0 mandatory spend, remain understandable to a student team, and work without external AI credentials or a hosted service.

## Decision

Build one local-first modular application using:

- Python for application and domain logic.
- FastAPI as the HTTP/application boundary.
- Plain HTML, CSS, and JavaScript served by the same application.
- SQLite for local session and answer history.
- Versioned JSON files for scenario and rubric definitions.
- A deterministic Python session controller as the sole authority for session state and allowed transitions.
- Deterministic feedback as the baseline; optional local-model assistance may be added behind a narrow interface only when useful and independently testable.

No additional runtime, hosted service, or architecture framework is required for the first MVP.

## Module boundaries

These are logical boundaries, not a requirement to create a separate file for every item immediately. Introduce a module only when the first vertical slice needs it.

### 1. HTTP / presentation boundary

Responsibilities:
- Render and serve the learner interface.
- Accept validated learner actions and return predictable responses.
- Translate domain errors into clear user-facing states.

Must not:
- Decide scenario transitions itself.
- Trust browser-supplied session state or feedback.
- call a model directly from route handlers.

### 2. Scenario loader and validator

Responsibilities:
- Load the selected versioned JSON scenario and rubric.
- Validate required fields, unique IDs, valid references, supported states, and transition targets before a scenario can be used.
- Expose an immutable, validated scenario definition to the session controller.

Rules:
- Store the scenario ID and version on each session.
- Existing sessions must remain associated with the scenario version they started with; editing a JSON file must not silently rewrite past attempts.
- Invalid or missing scenario data must fail clearly rather than silently falling back to a different scenario.

### 3. Session controller (domain authority)

Responsibilities:
- Own session lifecycle, current step, accepted answers, completion, and retry creation.
- Enforce allowed transitions and bounded scenario length.
- Select deterministic follow-up branches using explicit rules and validated answer/session context.
- Keep transcript ordering and session completion consistent.

Rules:
- The client and any model are never authoritative for state transitions.
- Empty answers, early finish/cancel, repeated submissions, invalid transitions, and already-completed sessions need defined behaviour and tests.
- Keep the first scenario small; do not create a general graph/workflow engine.

### 4. Persistence boundary

Responsibilities:
- Persist only the local records needed for session history, answers, scenario version, rubric/feedback version where relevant, and attempt comparison.
- Provide explicit deletion of a session and its dependent records.
- Keep storage access behind a small repository/data-access layer if that simplifies testing; do not add a generic repository framework.

Rules:
- SQLite is the only required database.
- Use parameterized SQL and database constraints where practical.
- Do not store raw audio in the text MVP.
- Do not transmit saved answers to external services.
- Deletion behaviour must be tested, including dependent answers and feedback.

### 5. Feedback engine and validator

Responsibilities:
- Produce formative checklist feedback for clarity, structure, specificity, follow-up handling, and conciseness.
- Tie each observation to actual answer text or a specific answer/turn reference.
- Include a concrete next action and an explicit “not enough evidence” state when the answer does not support a conclusion.
- Validate feedback shape and evidence references before displaying or saving it.

Rules:
- The deterministic baseline must work without any model installed or configured.
- Never invent a quote, evidence span, answer, or result.
- Do not infer intelligence, personality, emotion, confidence, employability, or hiring potential.
- Do not present checklist labels as validated psychometric scores or as an overall communication score.
- Malformed or unsupported generated feedback must be rejected or replaced by a clearly identified deterministic fallback, never displayed as trusted evidence.

### 6. Optional model adapter (not required for initial skeleton)

Responsibilities, if later implemented:
- Offer one narrow capability interface for a specific task, such as proposing follow-up wording or draft feedback.
- Keep provider-specific setup and failures outside the domain controller.
- Return structured suggestions that the application validates before use.

Rules:
- Missing configuration, model download, provider failure, timeout, or malformed output must not prevent the baseline text scenario from working.
- A model can suggest wording; it cannot change session state, choose unauthorized transitions, write directly to SQLite, or establish evidence that is absent from the learner's answer.
- No cloud provider or API key is a required dependency. No paid API, temporary credit, or pay-per-use service may be necessary.
- Do not build a general-purpose model gateway or multi-provider orchestration layer for the MVP.

### 7. Attempt comparison

Responsibilities:
- Compare two attempts of the same scenario and rubric version.
- Present answer/feedback differences and checklist states clearly.

Rules:
- Make the comparison transparent and task-specific.
- Do not imply that a change in one practice task proves general improvement or placement readiness.
- If the scenario or rubric versions differ, disclose the difference rather than presenting the attempts as directly equivalent.

## First vertical slice

The first demonstrable slice is:

1. Start the curated “Explain your project to a placement interviewer” scenario.
2. Submit text answers through a bounded set of deterministic steps/follow-ups.
3. Complete the session and review the ordered answers.
4. Receive checklist feedback grounded in the saved answers.
5. Start a retry using the same scenario and rubric version.
6. Compare the two attempts.
7. View local history and delete a session.
8. Run automated tests for the critical domain and privacy behaviour.

The app skeleton and tests must run without external AI credentials. A working UI is not considered complete if the session controller, feedback grounding, retry consistency, or deletion is missing.

## Data and privacy defaults

- Local-only session data; no mandatory account or hosted database.
- Collect only data needed for the practice loop.
- No raw audio capture/storage in this milestone.
- No external transmission of learner answers.
- Provide clear local-history deletion.
- Avoid logging full answer text by default; logs should help diagnose failures without duplicating learner content unnecessarily.
- Explain that feedback is formative and not an official university or hiring assessment.

## Testing and acceptance gates

Before the text MVP is considered complete, tests must cover:

- Scenario JSON validation, including invalid references and transitions.
- Allowed and forbidden session transitions.
- Empty, repeated, cancelled, early-finished, and completed-session actions.
- Answer ordering and scenario-version preservation.
- Feedback schema validation and evidence grounding (including fabricated/missing evidence rejection).
- Retry using the same scenario/rubric version.
- Attempt comparison when versions match and clear handling when they do not.
- Local persistence, session deletion, and deletion of dependent records.
- Baseline operation with no model configuration and graceful handling of optional-model failure.
- A fresh-checkout setup/run/test path documented in the repository.

The team must distinguish **implemented**, **automatically tested**, **manually demonstrated**, and **observed in a student pilot**. Passing tests alone does not prove learning effectiveness.

## Explicit non-goals for this decision

Do not add the following to deliver the first text MVP:

- React, Next.js, a frontend framework rewrite, or a second application runtime.
- LangGraph or another general workflow/agent framework.
- LiveKit, real-time voice rooms, mandatory STT/TTS, avatars, or audio storage.
- PostgreSQL, Redis, Kafka, Celery, queues, Kubernetes, microservices, or separate deployable services.
- Vector databases, RAG, knowledge graphs, CV/job-description ingestion, or company research.
- Authentication, institutional dashboards, public feeds, leaderboards, or multi-tenant cloud deployment.
- A large scenario library, spaced-repetition scheduler, or mastery system before the first loop and pilot justify them.
- Mandatory external AI APIs, paid hosting, subscriptions, or temporary free-credit dependencies.

These are explicit exclusions from the current milestone, not permanent claims that every future version must reject them.

## Consequences

### Positive
- The whole MVP can be understood and run as one local application.
- Core behaviour is deterministic and testable without a model.
- Scenario, session, feedback, persistence, and optional inference responsibilities have clear boundaries.
- The architecture preserves the option to test local voice or review features later without committing to them now.

### Trade-offs
- Deterministic follow-ups may initially be less conversational than a live agent.
- SQLite and local single-user operation are not a multi-user production deployment.
- A narrow interface may need to change when a measured future requirement appears; this is preferable to speculative abstraction now.
- Feedback quality still requires evaluation with real answers and, before any validation claim, appropriate human review.

## Revisit conditions

Reopen this ADR only when evidence from implementation, tests, hardware experiments, privacy review, or a student pilot shows a concrete limitation. Any proposed change must state the observed problem, smallest viable alternative, cost/hosting implications, migration impact, and tests that would prove the change. Upstream feature availability alone is not sufficient reason to change the architecture.

## Related decisions and source documents

- [Product and System Blueprint](PRODUCT_BLUEPRINT.md)
- [Complete Project Roadmap](COMPLETE_ROADMAP.md)
- [Research Review and Decision Matrix](RESEARCH_DECISION_MATRIX.md)
- [Upstream Repository Audit](UPSTREAM_REPOSITORY_AUDIT.md)
- [Upstream Feature Mapping](UPSTREAM_FEATURE_MAPPING.md)
