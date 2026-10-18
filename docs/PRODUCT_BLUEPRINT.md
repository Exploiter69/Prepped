# Prepped — Product Blueprint

**Status:** Product direction v1.0 — research synthesis, ready to guide the first implementation  
**Last updated:** 2026-10-19  
**Source research:** Claude, Gemini Deep Research, DeepSeek, Grok, and Perplexity reports archived under [`research/raw/`](../research/raw/).

> Prepped helps Indian engineering students practise important placement and professional conversations, get specific feedback tied to what they actually said, and improve through repeated practice.

This is the agreed product direction—not a claim that the software is already built or that learning outcomes have been proven.

## 1. The problem

Students can know technical concepts and still struggle to explain a project, answer interview questions clearly, organise an answer under pressure, or respond confidently to follow-up questions. Generic chatbots can help, but unstructured chatting does not guarantee realistic practice, useful feedback, or deliberate improvement over time.

Prepped will provide **structured conversation practice**: a realistic scenario, clear goal, a short session, evidence-linked feedback, and a practical next attempt.

## 2. Who we build for first

**Primary user:** Indian college engineering students preparing for placements, internships, project reviews, and professional communication.

**First job to be done:** “Help me practise explaining my project and answering follow-up questions before a real placement interview.”

**Initial scenario:** *Explain your project to a placement interviewer.* The interviewer asks a small number of relevant follow-ups based on the student's answers. The learner can retry after receiving feedback.

English is the first practice language. Keep the interface simple and allow clear, natural Indian English. Do not claim support for every Indian accent or language until tested.

### Why this starting point

- It is specific enough for a student team to implement and evaluate.
- Students can try it without institutional integrations or paid accounts.
- A repeatable scenario makes feedback and progress easier to compare than open-ended chat.
- It leaves a path to add HR interviews, technical explanations, presentations, teamwork, and difficult conversations later.

## 3. The core product loop

1. **Choose a scenario** with a clear goal and simple instructions.
2. **Practise** with a simulated interviewer. The first build may use text; voice is a planned capability, not a prerequisite for proving the scenario and feedback loop.
3. **Review the transcript** or answers from the session.
4. **Get actionable feedback**: what worked, what was unclear, and one or two concrete ways to improve.
5. **Retry the same scenario** and see whether the response improved against the same checklist.

The product's value is not “talk to an AI.” It is **practise → receive evidence-linked feedback → try again**.

## 4. Scope: what we will and will not build

### First working MVP

- One curated scenario: explaining a project to a placement interviewer.
- A guided session with a small number of interviewer turns and follow-up questions.
- Text input and responses, so the end-to-end learning loop can be tested without voice infrastructure.
- A transparent feedback checklist with examples quoted from the learner's answer.
- A retry flow using the same rubric.
- Local session history and a way to delete a session.
- A small test suite for scenario transitions, feedback structure, and data deletion.
- Optional local LLM support behind an interface; the basic demo must still run without a paid API.

### Add only after the first MVP works

- Local speech-to-text and text-to-speech.
- Voice practice with captions and interruption handling, once tested on available hardware.
- A second or third scenario based on student feedback.
- Local review cards for recurring improvement areas.
- Basic progress comparison across attempts.

### Explicitly out of scope for the first MVP

- Avatars, animated faces, lip-sync, or virtual worlds.
- Multi-agent simulations or a general-purpose graph platform.
- Institutional dashboards, cohort analytics, SSO, LMS integration, or enterprise features.
- Public social feeds, community features, or a marketplace.
- A huge scenario library, mobile apps, or multi-tenant cloud infrastructure.
- Fine-grained phoneme scoring, emotion detection, personality inference, or automated placement-readiness certification.
- Claims such as “improves placement chances by 40%” without a properly designed study.
- Mandatory paid APIs, subscriptions, hosted databases, or paid deployment.

These features may be reconsidered later only when user evidence, capability, and budget justify them.

## 5. Feedback and evidence rules

Prepped must not pretend that an AI-generated number is an objective measure of ability.

The first rubric uses observable behaviours, for example:

- **Clarity:** Can the learner explain the project's purpose in understandable terms?
- **Structure:** Does the answer cover the problem, approach, personal contribution, and result?
- **Specificity:** Does the learner give concrete details instead of unsupported claims?
- **Follow-up handling:** Does the answer respond to the actual question?
- **Conciseness:** Does the learner stay relevant without losing important context?

For each piece of feedback:

1. Quote or point to the learner's actual words.
2. Explain the specific issue in plain language.
3. Offer a concrete revision or practice action.
4. Say “not enough evidence” when the answer does not support a judgement.
5. Keep observations separate from conclusions. Do not infer personality, confidence, intelligence, employability, or future placement outcomes from one session.

Initially show a checklist and written reasoning, not a single “communication score.” If numeric scoring is explored later, compare it with human ratings first and document the limitations.

## 6. Architecture decision for the student MVP

**Choose the simplest local-first modular application. Do not implement the production architectures in the research reports wholesale.**

| Layer | First choice | Reason |
|---|---|---|
| Application/backend | Python + FastAPI | Familiar AI ecosystem and straightforward testing |
| Interface | Plain HTML, CSS, and JavaScript served by the app | Avoid a separate frontend build system until it is needed |
| Storage | SQLite | Local, zero-cost, no database server to operate |
| Scenario definition | Versioned JSON files | Easy to inspect, edit, and test |
| Scenario logic | Small deterministic state/turn controller | Predictable behaviour; no general graph engine |
| Feedback | Explicit rubric + validated structured output | Keeps feedback reviewable and testable |
| Optional local model | Ollama-compatible local endpoint behind an adapter | No paid API dependency; app must explain when no model is configured |
| Tests | Python standard test tooling / pytest | Exercise scenario flow, failure cases, and data handling |

Do not introduce PostgreSQL, Redis, queues, background-worker systems, microservices, Kubernetes, or a separate workflow engine for this MVP. They solve problems we do not yet have.

### Voice is a gated second milestone

Research consistently identifies voice as the long-term differentiator, but also flags latency, accent robustness, hardware, and model quality as real constraints. Do not assume that local voice will be fast or accurate enough on the available laptop.

After the text MVP passes user testing, run a small local feasibility spike:
- speech-to-text: compare a local Whisper implementation with another viable local option;
- text-to-speech: compare Piper and Kokoro on the actual machine;
- language model: benchmark a locally runnable model through the optional adapter;
- record response time, transcription errors, memory use, and whether the experience is usable.

Only choose a voice stack after this test. Do not use temporary free API credits as proof of a permanently zero-cost architecture. The product must remain usable in text mode if voice dependencies are unavailable.

## 7. Privacy and safe defaults

- Keep development and the initial demo local-first.
- Do not record or persist raw audio by default.
- Make session saving explicit and provide deletion.
- Do not send transcripts to external services without clear user awareness and consent.
- Treat learner responses as untrusted input; model text must never directly control application permissions or database operations.
- Validate structured model output and handle malformed or unavailable model responses gracefully.
- Do not collect sensitive personal details that are unnecessary for interview practice.
- Do not present generated feedback as a formal hiring decision or validated assessment.

Before any public deployment or collection of real student data, review applicable privacy obligations and deployment security.

## 8. Validation plan

Research is not proof of demand or learning impact. The first evidence must come from students trying the actual prototype.

### Small pilot

Recruit **10–20 student volunteers** if available. Explain that this is an early prototype, not a placement predictor. Ask them to complete the same scenario, read the feedback, and retry.

Record:
- whether they complete the session without help;
- which steps confuse them;
- whether feedback points to something actually present in their answer;
- whether they can produce a clearer second answer using the feedback;
- whether they would voluntarily use it again;
- bugs, failure cases, and time to complete.

Compare first and second attempts using the same transparent checklist. Keep raw counts and anonymised notes; do not turn a small convenience sample into a broad effectiveness claim. Report the sample size and limitations in any presentation.

### MVP acceptance checklist

- [ ] A new user can complete the one scenario from start to finish.
- [ ] Follow-up questions remain relevant to the learner's answer and scenario goal.
- [ ] Feedback references the actual answer and provides a concrete next step.
- [ ] The learner can retry and compare both attempts using the same rubric.
- [ ] Missing or broken local model configuration does not crash the application without explanation.
- [ ] Session data stays local by default and can be deleted.
- [ ] Tests cover the main flow, invalid model output, empty answers, and deletion.
- [ ] A pilot has been run and its findings are recorded honestly.

## 9. Build roadmap and decision gates

### Gate 0 — Product foundation
Write and review this blueprint, create the app skeleton, define the scenario JSON format, and agree on the feedback rubric.

**Exit:** a runnable app skeleton and a documented scenario/rubric.

### Gate 1 — One complete text scenario
Build the scenario flow, answer capture, follow-up logic, feedback checklist, retry, and local storage.

**Exit:** the MVP acceptance checklist for the core flow passes locally.

### Gate 2 — Test with students
Run the small pilot, fix confusing interactions, and inspect whether feedback is grounded and useful.

**Exit:** documented observations and a decision to iterate, narrow, or proceed. Do not require a predetermined positive result.

### Gate 3 — Local voice feasibility
Benchmark local STT, LLM, and TTS on the actual available hardware; preserve text mode as a fallback.

**Exit:** measured results and a documented go/no-go decision for voice.

### Gate 4 — Improve the learning loop
Add a second scenario and simple recurring-weakness review only if the pilot supports them.

**Exit:** repeat attempts can be compared consistently, and the feature demonstrably addresses a pilot finding.

### Later, not promised
Broader language support, more scenarios, validated scoring, mobile packaging, and institutional capabilities remain future options—not MVP commitments.

## 10. What the five research reports contribute

The reports are complementary research inputs, not five independent votes that make every proposal correct.

- **Claude — architecture:** supports clear module boundaries, versioned scenarios, evidence separated from judgement, testable state transitions, and staged implementation. Its production architecture is deliberately simplified here for a local student MVP.
- **Gemini Deep Research — voice and learning technologies:** contributes voice pipeline options, local speech tooling, scenario logic, and learning-science ideas. Performance figures and vendor/free-tier details must be rechecked on our hardware before being treated as guarantees.
- **DeepSeek — voice/AI engineering:** supports comparing cascaded STT → LLM → TTS with speech-to-speech, measuring latency and transcription quality, keeping providers replaceable, and validating feedback. Its managed-provider examples are not a requirement for this zero-spend project.
- **Grok — market gaps and product opportunities:** informs the scenario-based practice angle, feedback quality, accessibility, and the need to test whether users improve. Competitor observations are hypotheses to revisit, not proof of market demand.
- **Perplexity — product, learning loop, and roadmap:** contributes the practice → feedback → review → retry loop, competitor mapping, explicit MVP prioritisation, and human-anchored assessment. Its broader platform plan is narrowed to the first student use case.

### Shared conclusions we adopt

1. Start with a focused learner and a real practice task.
2. Make scenarios structured and testable rather than offering only open chat.
3. Tie feedback to observable evidence and avoid unvalidated scores.
4. Keep model and voice components replaceable.
5. Validate demand, usability, and feedback quality with real users.
6. Defer avatars, institutional tooling, and complex infrastructure.
7. Keep zero mandatory spend as a hard constraint and state the limits of local/free-tier systems honestly.

### Disagreements resolved for Prepped

- **Voice-first versus text-first:** voice is the long-term direction, but text is the first implementation gate so the core learning loop can be tested before taking on audio latency and hardware risks.
- **Managed free tiers versus strictly local:** the reports discuss both; this project chooses local-first and no mandatory paid API. Free quotas may be used only for explicitly optional experiments, never as a dependency.
- **Production architecture versus student scope:** production reports recommend durable workers, service boundaries, and more sophisticated infrastructure. The MVP uses one local application, SQLite, JSON scenarios, and a deterministic controller.
- **Broad multi-skill platform versus a narrow wedge:** the long-term idea can grow, but the first use case is project explanation in a placement interview.

## 11. Rules for future decisions

Every proposed feature must answer:
1. Which real student problem does it address?
2. What is the smallest version we can test?
3. Can it be built and run with no mandatory spending?
4. How will we know it works?
5. What existing work or complexity can we avoid?

If there is no clear answer, defer the feature. GitHub is the source of truth; record meaningful product or architecture changes here before expanding scope.

---

**Current decision:** build one local text-based project-interview practice flow with evidence-linked checklist feedback and retry. Test it with students. Then measure whether local voice is feasible on the actual hardware.