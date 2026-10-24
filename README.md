# Prepped

**Prepped helps Indian engineering students practise placement and professional conversations, get specific feedback tied to their answers, and improve through repeated practice.**

Prepped is being restarted from a clean, evidence-led scope. The first version is a **local, text-based project-interview practice flow**. Voice is a later milestone gated on measured local-hardware feasibility. The project does not claim validated placement outcomes or assessment accuracy.

## Start here

1. [Complete Product and System Blueprint](docs/PRODUCT_BLUEPRINT.md) — product, user flows, rubric, architecture, privacy, testing, and scope.
2. [Architecture Decision Record 001](docs/ADR-001-MINIMAL-LOCAL-FIRST-ARCHITECTURE.md) — accepted stack, module boundaries, data/privacy defaults, acceptance gates, and explicit non-goals for the first MVP.
3. [Complete Project Roadmap](docs/COMPLETE_ROADMAP.md) — implementation gates, pilot, voice feasibility, and semester-by-semester TDP outcomes.
4. [Research Review and Decision Matrix](docs/RESEARCH_DECISION_MATRIX.md) — what each AI report contributes and what we adopt, defer, reject, or re-verify.
5. [Research archive verification](research/raw/VERIFICATION.md) — what is exact and what PDF/OCR limitations remain.
6. [Upstream repository audit](docs/UPSTREAM_REPOSITORY_AUDIT.md) — source-inspected dependencies, licenses, offline-mode claims, CI evidence, and audit limitations.
7. [Upstream feature mapping](docs/UPSTREAM_FEATURE_MAPPING.md) — feature-by-feature reuse/adapt/build/defer/reject decisions against Prepped's blueprint.

## Original AI research

- [Claude architecture research](research/raw/claude.md)
- [Gemini Deep Research report](research/raw/gemini-deep-research.md)
- [DeepSeek voice/AI research](research/raw/deepseek.md)
- [Grok competitor research](research/raw/grok.md)
- [Perplexity product research dossier](research/raw/perplexity.md)
- [Preserved original source files and PDFs](research/raw/originals/)

The original reports are inputs, not a specification to implement wholesale. Their recommendations conflict on product scope, text versus voice, architecture complexity, and managed versus local services. The decision matrix records how those conflicts were resolved.

## First MVP

One scenario: **Explain your project to a placement interviewer.**

The learner answers a few questions, receives feedback tied to their actual words, retries using the same transparent checklist, compares attempts, and can delete local session history. The first version prioritises a working, testable learning loop over real-time audio, avatars, social features, institutional dashboards, or a large scenario library.

## Project constraints

- ₹0 mandatory spending: no required paid APIs, subscriptions, hosting, or usage-based services.
- Local-first development with a small, understandable architecture.
- Initial stack: Python + FastAPI, plain HTML/CSS/JavaScript, SQLite, and versioned JSON scenarios.
- Optional local AI must not be required for the app skeleton or deterministic scenario tests to work.
- No unsupported claims about placement rates, validated skill scores, or learning effectiveness.
- No raw audio storage by default; privacy and deletion are part of the design.
- GitHub is the source of truth.

## Current status

**Research archived and reviewed; product direction, architecture decision, and roadmap documented; application implementation has not yet been established.**

The next milestone is one complete local text scenario with evidence-linked feedback, retry, attempt comparison, local history, deletion, and automated tests. See the [Complete Roadmap](docs/COMPLETE_ROADMAP.md).
