# Phase I — Voice Intelligence & Contextual Coaching

**Status:** Implementation added to `feature/learner-profile`; local pytest on commit `c4200e5fc06ccfcd06c9b49fadc6cc8d6ac9afdc` reports 145 passed, 0 failed, and one Starlette/httpx deprecation warning. Exact-commit GitHub Actions [run 44742961672](https://github.com/Exploiter69/Prepped/actions/runs/44742961672) passed with 143 passed, 2 optional voice skips, and 1 warning. Manual target-laptop acceptance remains open. This record must be updated with the final CI run and observed device checks before Phase I is marked accepted.  
**Architecture:** Existing FastAPI + SQLite + plain HTML/CSS/JavaScript modular monolith.  
**Persistence:** No Phase I database migration or new table. Existing saved session JSON snapshots remain readable.  
**Cost:** No new paid API, subscription, hosting, model, or required service.

## Delivered implementation

### I1 — Voice request lifecycle and recovery

- Project Practice voice controller now uses AbortController for in-flight TTS and STT requests.
- Changing the active question/workspace or leaving the page cancels the outstanding request, stops active capture, releases streams, and prevents stale responses from changing the current screen.
- Career Studio prompt playback now has a request identity, AbortController cancellation, stale-response guards, and object-URL/audio cleanup.
- Career prompt playback is cancelled on Stop, prompt change, workspace navigation, and page unload.
- Project Practice recorder start failures are caught and cleaned up; the text answer path remains available.
- Existing G.1 deferred microphone permission protections remain in place.
- Remote Groq disclosure remains visible before Career capture; local mode remains local and does not silently fall back to remote transcription.
- Raw audio is not added to application persistence.

### I2 — Contextual follow-ups and response coaching

- Career content version 1.2.0 adds an authored contextual follow-up rule, simpler wording, and a clarification hint for each of the 12 primary questions and their follow-ups across Project Explanation, HR/Behavioural, and Technical Fundamentals.
- Learners can switch between original and simpler wording, reveal/hide an authored prompt hint, and replay the spoken prompt. The selected wording is recorded with the answer so review reflects the prompt actually shown.
- After a retry, the review compares matching previous/current answer pairs side by side. The comparison is descriptive and carries an explicit no-measured-improvement statement.
- The backend validates each contextual rule against an explicit trigger allowlist.
- Follow-up selection checks a small set of text cues (example, first-person action, reasoning, evidence, sequence, reflection, preparation, and trade-off markers). If the cue is not detected, the authored contextual prompt is selected; otherwise the existing guided/standard/challenging prompt remains the fallback.
- The UI displays why a contextual follow-up was selected and states that the cue may miss equivalent wording and is not an assessment.
- Every Career feedback turn now includes one possible next action, a short basis/limitation statement, and (when available) a relevant excerpt from the learner's own answer.
- When a learner retries a completed studio, the next review shows previous and current answers side by side for matching prompts. It explicitly avoids claiming that differences are measured improvement.
- Existing checks remain text-cue reflections. No overall score, correctness rating, technical answer key, proficiency level, pronunciation score, or hiring prediction was introduced.

### I3 — Learner-controlled Memory and plan handoff

- Each review note retains the existing explicit **Save answer to learning memory** action.
- Learners can separately choose **Save coaching action to learning memory**. This uses the existing Memory API and source metadata; no automatic capture occurs.
- A completed Career review offers **Add next practice to today's plan**. If today's plan does not exist, the learner's click creates it using the existing 30-minute default; then the selected studio is added through the existing adaptive-plan API.
- The plan item represents a future practice session. It is completed only by a new linked Career session created after the item, consistent with Phase H's source-activity completion rules.
- No duplicate learner profile, evidence table, plan table, or workflow system was added.

## Automated verification added

- `tests/test_career.py`: contextual cue selection versus difficulty fallback; authored contextual prompt validation; simpler-prompt persistence; retry comparison; answer-specific coaching structure and absence of an aggregate score.
- `tests/test_browser_acceptance.py`: Career and Project Practice TTS cancellation; Career and Project Practice STT cancellation; prompt-hint/simpler-wording controls; retry comparison rendering; adaptive-plan handoff.
- `tests/test_voice.py`: browser voice source exposes abortable TTS/STT request controllers.
- `tests/test_browser_acceptance.py`: Career prompt synthesis is aborted on navigation; Project Practice prompt synthesis is aborted on navigation; completed Career review can add the next practice to the existing adaptive plan.
- Existing browser tests continue to cover deferred microphone permission cancellation and stream cleanup in Learning and Career.
- **Local verification:** commit `c4200e5fc06ccfcd06c9b49fadc6cc8d6ac9afdc`; `python -m pytest -q` — **145 passed, 0 failed, 1 warning** (170.29s). The warning is Starlette's deprecation notice for httpx-backed TestClient use.
- **Exact-commit GitHub Actions:** [run 44742961672](https://github.com/Exploiter69/Prepped/actions/runs/44742961672) — **143 passed, 2 skipped, 1 warning** on the exact Phase I commit. The two skips require optional `espeak-ng` on the hosted runner; the warning is Starlette/httpx TestClient deprecation. Python compilation, JavaScript syntax checks, dependency consistency, dependency audit, Chromium setup, and browser tests passed. A passing test suite does not replace target-device acceptance.

## Manual target-laptop acceptance checklist

- [ ] Start Prepped from the documented clean local setup; confirm text practice works with STT and TTS unavailable.
- [ ] In Project Practice, play a prompt, stop it, replay it, and navigate to Career while a prompt request is pending. Confirm no late audio starts.
- [ ] Record a short Project Practice answer using the configured local STT engine. Confirm the transcript is editable and only the edited text is submitted.
- [ ] Cancel/navigation during transcription in both Project Practice and Career; confirm the in-flight request is aborted and no stale transcript is inserted into a different question or workspace.
- [ ] Deny microphone permission, disconnect/unavailable microphone, and retry. Confirm a clear recovery message and usable text fallback.
- [ ] In Career, repeat the playback stop/replay/navigation checks. Confirm microphone tracks stop when leaving the workspace.
- [ ] For each studio, toggle simpler wording, reveal/hide the authored prompt hint, replay the prompt, and confirm the answer review records the wording actually shown.
- [ ] Complete one session in each of the three studios. Confirm follow-ups remain relevant and the explanation is shown when a contextual cue selects one.
- [ ] Try equivalent wording without the literal cue phrases. Observe where the heuristic misses it; record findings without treating them as learner errors.
- [ ] Review coaching for each answer. Confirm it refers to the submitted answer, is phrased as one possible improvement, and does not present correctness or a score.
- [ ] Explicitly save an answer and a coaching action to Memory. Confirm each appears with Career source metadata; edit and delete them.
- [ ] Complete a studio, retry it, and compare the previous/current answer pairs. Confirm the UI makes no automatic improvement claim.
- [ ] Add a future studio practice to today's plan. Complete a new session after the plan item exists and confirm plan completion derives from that saved session.
- [ ] If Groq is configured, verify disclosure appears before capture and that only the selected provider receives the recording. Otherwise verify Vosk remains local.
- [ ] Confirm no raw audio file or database row is created by the default transcription path.
- [ ] Review keyboard focus, screen-reader announcements, 375 px layout, and visible text alternatives across Project Practice and Career.

## Known limitations and non-claims

- Text cue detection is intentionally simple. It may miss semantically equivalent wording and may match weak or irrelevant content. The learner must interpret suggestions.
- Coaching is deterministic formative reflection, not expert evaluation, technical correctness checking, or an AI tutor.
- No validated speech accuracy, accent quality, pronunciation score, English proficiency, CEFR level, confidence diagnosis, learning gain, interview performance, or placement outcome is claimed.
- No LLM, realtime duplex voice, streaming transcript, always-on microphone, voice activity detection, or cloud service is required or added.
- Optional Groq sends audio to the provider when configured; current provider data handling must be checked against its current terms. Prepped does not claim control over provider retention.
- Manual microphone/STT/TTS checks and target-laptop accessibility checks remain open until a human records them.

**Acceptance rule:** mark Phase I fully accepted only after exact-commit CI is green, the manual checklist is completed on the target laptop, any material defects are fixed, and the observed limitations are recorded in CURRENT_STATE.md.
