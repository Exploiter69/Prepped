# Prepped — Upstream Repository Audit

**Audit date:** 2026-10-24  
**Purpose:** Complete step 1 of the upstream-reuse plan before changing Prepped's architecture or importing code.  
**Repositories reviewed:** DeepInterview, AI Mock Interviewer, Sotto.  
**Method:** Current public GitHub pages, README and architecture documentation, root/application manifests, Python project manifest, Docker Compose configuration, selected service/database/test files, and license files.  
**Execution status:** Source inspection completed. Dependency installation and test suites were **not run in this environment**: direct Git clones failed because this environment could not resolve github.com. Findings below distinguish source-inspected/documented behavior from independently executed tests.

## Executive conclusion

Do not merge any of these applications wholesale into Prepped.

- **DeepInterview:** strongest architectural reference for separating preparation, conversation turns, and post-session feedback; its mock-first provider adapters are worth studying. Its full voice stack and web framework are too large for Prepped's first MVP.
- **AI Mock Interviewer:** closest practical reference for a local interview lifecycle, SQLite persistence, provider fallback, and focused service tests. Best candidate for selective code-level reuse, subject to file-by-file review and preserving MIT notices.
- **Sotto:** strongest reference for later learning/review design: spaced repetition, mastery gates, learner notes and adaptive practice. Do not copy its application stack. Its current main license is PolyForm Noncommercial 1.0.0, and its runtime stack includes PostgreSQL and Redis.
- **Prepped remains the source of truth.** Keep the planned Python/FastAPI + plain HTML/CSS/JS + SQLite + versioned JSON approach unless an actual MVP requirement proves a change is necessary.

## 1. DeepInterview

Repository: https://github.com/ngoanpv/DeepInterview  
Architecture: https://github.com/ngoanpv/DeepInterview/blob/main/docs/ARCHITECTURE.md  
License: https://github.com/ngoanpv/DeepInterview/blob/main/LICENSE  
Notice: https://github.com/ngoanpv/DeepInterview/blob/main/NOTICE

### Product and code structure

DeepInterview is a voice-first mock interview platform that prepares a question plan from a CV and job description, conducts an adaptive interview, then scores/coaches the candidate. Its architecture separates three phases:

1. **Prep:** parse CV/JD, optionally research the company, construct shared interview context and a question plan.
2. **Live:** ask, listen, save answers and advance questions; keep the turn path lean.
3. **Post:** evaluate competencies, coach language, create a report, and feed weak areas into future practice.

A shared contract is defined in TypeScript and mirrored in Pydantic, with parity tests. External providers sit behind interfaces and deterministic mock adapters are the default.

### Stack and dependencies inspected

- Root workspace: pnpm, Turbo and TypeScript.
- Web app: Next.js 16, React 19, Tailwind CSS 4, LiveKit client/server SDKs, Supabase clients, S3 SDKs, Zod and UI/data-visualization libraries.
- Agent: Python 3.11+, FastAPI, Uvicorn, Pydantic, HTTPX, LangGraph, LangChain Core and MarkItDown for CV document parsing.
- Optional provider extras include Google/Gemini, OpenAI, Supabase, Tavily, and a substantial LiveKit worker set with STT/TTS/LLM plugins.
- Docker Compose base stack includes web, agent API and a LightRAG knowledge sidecar. Optional profiles include live voice and local inference services.

This is a multi-package, multi-process stack—not a sensible foundation to transplant into Prepped's first MVP.

### License

The root LICENSE and package manifest identify **Apache-2.0**. Preserve license, copyright and NOTICE obligations if code is copied. Check individual licenses for specific assets, datasets, avatars, models and nested components; do not assume the repository-level license clears every third-party item.

### Offline operation

The README says build and prep/live/post pipelines can run without provider keys using mock adapters, and that the base Docker Compose stack can come up in that mode. This is an offline **test/demo path**, not the same as running a real model-generated interviewer.

- **No-key mock path:** exercises contracts, flows and reports with deterministic mock behavior.
- **Real voice path:** gated behind the live profile; requires LiveKit plus STT/TTS/LLM provider configuration.
- **Local-model path:** an optional local profile supports Ollama, faster-whisper and local TTS components. It requires downloading images/models and is heavier than the mock path.
- Company research and real external provider calls should not be assumed to work offline.

### Tests and useful lessons

The repository documents TypeScript tests, Python/Pydantic contract-parity tests and pipeline tests. I inspected the architecture and manifests but did not execute the suites.

Useful lessons for Prepped:
- Keep the first interaction loop small and bounded.
- Separate conversation control from feedback/evaluation.
- Use stable, validated contracts between UI, session logic and feedback.
- Keep external providers behind replaceable adapters.
- Use deterministic mock/fallback behavior to test core flows without credentials.

Do not import the multi-agent graph, LightRAG sidecar, Supabase, S3/R2, LiveKit worker, avatar features or Next.js frontend into the MVP merely because DeepInterview uses them.

## 2. AI Mock Interviewer

Repository: https://github.com/iarsingh/ai-mock-interviewer  
Services: https://github.com/iarsingh/ai-mock-interviewer/tree/main/src/services  
Tests: https://github.com/iarsingh/ai-mock-interviewer/tree/main/tests  
License: https://github.com/iarsingh/ai-mock-interviewer/blob/main/LICENSE

### Product and implementation inspected

The app is a local-first technical interview practice tool. It supports topic-based practice, fixed mock sets, typed answers, optional browser speech, saved progress and optional AI feedback. Its README describes offline template feedback and a built-in question bank.

The inspected interview service supports creating, retrieving, starting, advancing, answering and completing a session. It validates topics, bounds duration/question limits, stores interview configuration and delegates question generation to an injected gateway. A service test uses an in-memory SQLite database and deterministic fake gateway to check persistence, topic rotation, answer submission and completion.

The SQLite factory creates separate tables for interviews, topics, questions and answers, with foreign keys, indexes and cascade behavior. This is a useful small reference for Prepped's own session persistence and deletion tests.

### Stack and dependencies inspected

- Runtime: Node.js using the built-in HTTP server rather than a full web framework.
- Frontend: vanilla HTML/CSS/JavaScript.
- Persistence: SQLite via better-sqlite3; local account fallback uses a git-ignored JSON file. PostgreSQL is supported for hosted account storage.
- Optional model integration: Ollama and cloud-provider SDK support.
- Optional job-description parsing: PDF, DOCX and OCR packages (pdf-parse, mammoth, tesseract.js).
- Browser speech uses browser Speech Synthesis and Speech Recognition APIs.
- Current package.json and lockfile specify Node >=22 <23. Some rendered README sections have inconsistent setup details, so use the manifest and lockfile as the source of truth for the current Node requirement.

### License

The root LICENSE and package manifest say **MIT**. Code reuse is permitted subject to retaining the copyright and license notice in copies or substantial portions.

Review the large question-bank and generated-document files separately before copying content. A repository-wide MIT label does not independently establish the provenance or rights status of every included question, excerpt or generated dataset.

### Offline operation

The documented start:offline mode forces OFFLINE_ONLY=1, uses the built-in question bank and deterministic/template feedback, and does not require a cloud AI key. Typed practice can continue without browser speech recognition.

Qualifications:
- Dependencies must already be installed; initial installation needs package access.
- Browser speech recognition is not guaranteed to be offline and may use an internet-backed browser service.
- Ollama avoids cloud inference after the model is downloaded, but requires a separate local model and sufficient hardware.
- Hosted production mode has additional persistence and secret requirements; local SQLite is not a drop-in substitute for a durable hosted database.
- The app logs answer text and feedback locally by default in development unless disabled. Prepped should make its own saving/logging behavior explicit and testable.

The best baseline to borrow is **typed local practice plus deterministic fallback**, not the assumption that every voice or hosting feature works offline.

### Tests and useful lessons

The repository has Node's built-in test runner, service-level tests, a repository hygiene/release check and a documented local readiness endpoint. The inspected service tests use a fake AI gateway, a good pattern for reliable tests without a model or API key.

Useful lessons:
- Inject a question/feedback provider instead of coupling it to session control.
- Test session transitions and persistence with a temporary or in-memory SQLite database.
- Bound session length and user-provided text.
- Keep a deterministic no-credentials path as a first-class product mode.
- Treat transcripts and logs as private data; avoid silently logging more than necessary.

Do not import its account system, PostgreSQL deployment path, browser speech-recognition dependence, job-description upload/OCR, extension or large question bank into Prepped's first slice.

## 3. Sotto

Repository: https://github.com/affromero/Sotto  
License: https://github.com/affromero/Sotto/blob/main/LICENSE  
Main package manifest: https://github.com/affromero/Sotto/blob/main/package.json  
Compose stack: https://github.com/affromero/Sotto/blob/main/docker-compose.yml

### Product and implementation inspected

Sotto is a self-hosted language-learning system. Its documented learning loop includes CEFR placement, levelled course progression, mastery gates, practice across skills, learner notes, a vocabulary memory graph, spaced repetition, adaptive listening and spoken conversation. These are useful **learning-design ideas**, but its product domain and implementation are broader than Prepped's initial project-interview scenario.

### Stack and dependencies inspected

- Node 24 workspace with Next.js/React, TypeScript, Prisma, PostgreSQL/pgvector, Zod and a large web dependency set.
- Redis and BullMQ/Ioredis for background work.
- Multiple packages/workspaces and separate services, including speech and model integrations.
- Docker Compose base includes PostgreSQL and Redis and a browser automation sidecar.
- Optional local inference profile includes Ollama, faster-whisper and a Kokoro TTS service.
- The package scripts run a substantial unit/integration/browser/type-check/build suite.

This is too much infrastructure for Prepped's current hardware and zero-extra-service MVP constraints. Adopting Redis/BullMQ or PostgreSQL would be a deliberate architecture change, not a harmless feature addition.

### License — important restriction

The current root LICENSE and package manifest specify **PolyForm Noncommercial 1.0.0**. It permits specified noncommercial purposes, including personal study and use by educational institutions, but is not a general commercial-use license. The README also flags separately licensed components, including an AGPL speech service and MIT submodules.

For Prepped:
- Do not copy Sotto application code into a project that may later be commercialized without resolving license and intended-use implications with rights holders or qualified legal advice.
- If studying ideas, implement general learning concepts independently and document the source of inspiration.
- If considering a component, inspect its own license, notices and dependency terms first. The root license does not clear every submodule or service.

This is a practical blocker for copying Sotto code into a future commercial Prepped product, even though its learning design is valuable.

### Offline operation

Sotto documents a fully local AI profile with Ollama, faster-whisper and Kokoro, so inference need not use cloud API keys after models/images are acquired and configured. Its normal self-host setup still depends on a larger local service stack. Model downloads, container images, dependency installation and first-time setup require connectivity unless cached already.

“Offline-capable” does not mean lightweight, easy to run on a laptop with limited RAM, or free of setup and maintenance costs. Local speech models and the service stack need real hardware measurements before they can be recommended for Prepped.

### Tests and useful lessons

The project documents a broad test/type-check/build pipeline and has explicit learning-model packages. I inspected manifests, schema and service configuration, but did not execute its suite.

Useful lessons for a later Prepped learning stage:
- Store learning evidence from each attempt, not only a single score.
- Tie review actions to specific observed weaknesses.
- Add spaced repetition only after the initial practice-and-feedback loop produces useful evidence.
- Gate progression on clear, explainable criteria rather than opaque model judgments.
- Keep learning policy separable from UI and session storage.

Do not copy the vocabulary graph, course engine, Prisma schema, worker stack or service architecture into the MVP.

## Cross-repository comparison

| Area | DeepInterview | AI Mock Interviewer | Sotto |
|---|---|---|---|
| Main purpose | Voice-first mock interviews | Local technical interview practice | AI language learning |
| Primary stack | Next.js/React + Python/FastAPI | Node + vanilla web + SQLite | Next.js/React + Prisma/Postgres + Redis |
| Repository license | Apache-2.0 | MIT | PolyForm Noncommercial 1.0.0 |
| No-key path | Mock adapters for pipeline/demo | Built-in questions + template feedback | Local models after installation/configuration |
| Real local AI | Optional local inference profile | Optional Ollama | Explicit Ollama + local STT/TTS profile |
| Voice fully offline by default? | No; real live worker needs configuration | No guarantee; browser STT may use internet | Intended local voice path, but needs models/services |
| Best lesson for Prepped | Prep/live/post boundaries; adapters | Session lifecycle; SQLite; deterministic tests | Review, mastery and spaced repetition |
| MVP fit | Patterns only | Closest code-level reference | Learning concepts only for now |

## Cross-cutting findings

### 1. “Offline” has three distinct meanings

For future docs and tests, distinguish:
1. **No cloud credentials:** app starts and core flows work without API keys.
2. **No external inference:** model processing is local or deterministic; no transcript is sent to a provider.
3. **Air-gapped operation:** app works after dependencies, models and assets are installed, with networking unavailable.

Prepped's first release should prove levels 1 and 2 for typed practice. Air-gapped behavior must be tested explicitly, not inferred from a setting named “offline.”

### 2. Start with deterministic feedback

Use a tested deterministic feedback structure for the first rubric and put any optional model behind an interface later. An LLM must not be required to start/finish a session, view prior attempts or delete saved data.

### 3. Make privacy visible and minimal

Prepped should define and document whether attempts are transient or saved by default; which transcript/feedback fields persist; whether logs are written; how session-linked data is deleted; whether audio is stored (the text-only stage should not store audio); and whether an external provider receives learner text. Disclose and require explicit opt-in before enabling that provider path.

### 4. Test failure modes, not only happy paths

Initial tests should cover session transitions, bounded follow-up turns, empty/oversized answers, feedback schema validation, malformed model output, no-provider fallback, same-rubric retry comparisons, and deletion of session-linked records. Green tests using mocks do not prove real provider or real-time voice operation.

## Public CI status snapshot

I also inspected recent GitHub Actions history as a separate signal. This is **not** a substitute for running the projects on Prepped's target laptop, and a successful workflow must be interpreted by its workflow name and commit.

- **DeepInterview:** recent dependency-update checks for root formatting/types/tests, agent and LightRAG Python/Docker, and web Docker completed successfully around 2026-10-19. Example: https://github.com/ngoanpv/DeepInterview/actions/runs/39324853529
- **AI Mock Interviewer:** the main-branch CI run listed for commit 0f14400f completed successfully on 2026-10-15; a subsequent dependency-update CI run also succeeded on 2026-10-18. Example: https://github.com/iarsingh/ai-mock-interviewer/actions/runs/38736828775
- **Sotto:** production-image and several dependency-update workflows for commit 17a31623 completed successfully on 2026-10-23/24. A separate CI workflow on a Dependabot branch failed on 2026-10-23; that failure should not be represented as a failure of main, but it is a reminder that a dependency update can break checks. Example successful production-image run: https://github.com/affromero/Sotto/actions/runs/40060596800

These results show active automated maintenance and some recent passing checks. They do not establish that every suite passed on the exact same commit, that real voice works offline, or that an air-gapped installation succeeds.

## Audit limitations and confidence

**Verified by source inspection:** root license declarations/files; root and application manifests; documented runtimes and dependency families; selected Compose services; selected SQLite and interview-service implementation; example service tests; documented offline modes.

**Not independently verified:** successful clean installs; actual execution of any test suite; actual offline/air-gapped runs; model latency or RAM use; exhaustive licenses for every transitive dependency, nested service, dataset, model, font, image or media asset; whether every README claim matches runtime behavior.

Direct clone attempts failed because this environment could not resolve GitHub. Before copying code, clone a pinned commit in the implementation environment and run relevant tests locally. Record commit SHAs and an SBOM/license inventory for code actually adopted.

## Decision for the next Prepped stage

1. Keep Prepped's planned stack and first-scenario scope unchanged.
2. Use AI Mock Interviewer's session lifecycle, SQLite testing approach and injected deterministic gateway as the first code-level reference.
3. Use DeepInterview's prep/live/post boundary and provider-adapter idea only where it fits the small text flow.
4. Keep Sotto as a learning-design reference for a later review milestone; do not import its code or infrastructure.
5. This audit alone does not approve code imports. Any proposed reuse must identify source path, commit SHA, license, attribution, modifications and tests.

**This document completes the source-inspection portion of Step 1. It does not claim the three upstream projects were installed or tested locally.**
