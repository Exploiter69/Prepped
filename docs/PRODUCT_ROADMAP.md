# Prepped — Product Roadmap

**Product direction:** A complete, local-first learning and career-readiness platform for Indian engineering students and early-career learners.

**Engineering principle:** Build a coherent product on the existing FastAPI + SQLite + HTML/CSS/JavaScript foundation. The existing practice room remains a working module. This roadmap expands it; it does not authorize a rewrite.

## Product promise

Prepped helps a learner become more capable at communicating, explaining technical work, learning English, and handling placement and early-career conversations through deliberate practice, feedback grounded in their own responses, review, and visible progress.

It is a practice and learning tool, not a hiring assessment, placement predictor, or substitute for a qualified teacher.

## Product modules

### 1. Learner workspace and personalisation
- One private local learner profile; no account or login requirement.
- Onboarding: current study year, branch, learning goals, confidence/starting level, target role, and focus areas.
- Editable preferences and goals.
- A baseline diagnostic that records what the learner can currently do; it must not claim validated proficiency.
- Practice recommendations derived transparently from goals, recent activity, and observed evidence.
- Learner can skip onboarding and continue to the existing practice room.

### 2. Learning paths and skill map
- Skills grouped into English communication, professional communication, project explanation, interview readiness, and technical communication.
- Learning paths broken into small lessons, guided practice, and review.
- Clear prerequisite and progression rules; no opaque level score.
- Content stored as versioned local JSON so scenarios can be authored and reviewed without a CMS.

### 3. English and communication studio
- Everyday and professional English.
- Sentence construction, grammar-in-context, vocabulary, clarity, structure, conciseness, and confidence-building practice.
- Explain, summarise, describe, compare, clarify, ask questions, and give opinions.
- Pronunciation/listening exercises only where the installed local speech tools can support them; never invent accuracy scores.
- Corrections explain the issue and offer examples, not just a red/green judgement.

### 4. Interview and career studio
- Project explanation and personal contribution.
- HR and behavioural questions.
- Technical interview scenarios and concept explanations.
- Role- and domain-specific question sets.
- Follow-up questions and multi-turn mock interviews.
- Resume/project discussion practice can be added as a local document workflow later; no automatic hiring claims.

### 5. Voice-first tutor and practice room
- Spoken prompts, record/stop capture, editable transcripts, spoken playback, and text fallback.
- Local Vosk STT and Piper/espeak TTS remain the default direction.
- Optional provider adapters may be added only when explicitly configured; remote processing must be clearly disclosed.
- Voice failures never block text practice.
- No raw audio retention by default.
- Turn-based roleplay and scenario state are deterministic and testable before any optional generative tutor is introduced.

### 6. Personal learning memory and revision
- Save vocabulary, useful phrases, corrections, recurring mistakes, and weak concepts with learner consent/actions.
- Convert selected items into revision cards.
- Spaced repetition with a small, transparent local scheduler (FSRS-inspired only if implemented and tested; do not claim FSRS compatibility without it).
- Review queue, due dates, card editing, suspend/delete, and source context.
- Revisit errors in future practice without silently changing submitted answers.

### 7. Progress and insights
- Activity history and completed learning sessions.
- Progress by skill using explainable evidence and counts, not a misleading single score.
- Recurring patterns and recently practised topics.
- Review completion, consistency, and personal goals.
- Recommendations show why they were suggested and let the learner dismiss them.
- Export/backup and restore of local learning data before broad use.

## Delivery sequence

### Foundation — Learner workspace (next)
1. SQLite learner profile with additive migration.
2. Profile read/update API and validation.
3. Accessible onboarding/edit interface; profile remains optional.
4. Tests for validation, persistence, and compatibility with existing sessions.

### Learning foundation
1. Skill taxonomy and versioned content manifest.
2. Scenario catalogue and reusable scenario runner.
3. Learner baseline diagnostic with transparent, non-certified output.
4. Rule-based recommendations connected to profile and practice history.

### Communication and interview studios
1. English micro-practice scenarios.
2. Professional communication and project explanation tracks.
3. HR/behavioural and technical interview scenario packs.
4. Multi-turn follow-up logic and mock-interview session review.

### Learning memory
1. Vocabulary/phrase and correction capture.
2. Mistake and weak-concept capture with explicit evidence/source.
3. Editable review cards and local spaced-repetition scheduler.
4. Review sessions integrated with learning paths.

### Progress and product hardening
1. Skill-level activity and evidence views.
2. Goal tracking and explainable recommendations.
3. Local data export/import and recovery.
4. Accessibility, responsive UX, security/privacy review, performance and fresh-install checks.
5. Documented manual acceptance on the target laptop and a small consent-based student usability study when available.

## Architecture and hard constraints

- Required runtime: Python 3.11+, FastAPI, SQLite, plain HTML/CSS/JavaScript.
- Existing app modules and session data must remain compatible; use additive database migrations.
- Keep a modular monolith and one SQLite database.
- ₹0 mandatory operating cost. No paid APIs, subscriptions, hosted database, or remote service as a required dependency.
- No mandatory login/accounts, React/Vue/Svelte, Redis, Kafka, Celery, Kubernetes, microservices, vector database, or second workflow engine.
- Local speech models are optional explicit installs; do not download model weights during startup.
- Do not store raw audio by default. Clearly disclose any optional remote processing.
- Avoid collecting unnecessary sensitive personal data. Profile information stays local.
- Keep GitHub as code source of truth. Never discard or overwrite a user's uncommitted local work.

## Product quality gates

Every module must have:
- A clear learner outcome and complete usable flow, not just a static screen.
- Server-side validation and persistence where data is involved.
- Automated tests for core behaviour, failure cases, and legacy compatibility.
- Accessible labels, keyboard operation, useful empty/loading/error states, and responsive layout.
- Documentation distinguishing implemented, tested, manually verified, and planned.
- Honest feedback: quote submitted evidence, explain uncertainty, and avoid unsupported proficiency or outcome claims.

## Explicitly not claimed

Until separately implemented and validated, Prepped does not claim expert-level AI tutoring, certified CEFR/IELTS proficiency, accurate pronunciation grading, emotion/personality detection, placement probability, or measured learning outcomes. Optional generative AI must not be a mandatory dependency or fabricate feedback evidence.
