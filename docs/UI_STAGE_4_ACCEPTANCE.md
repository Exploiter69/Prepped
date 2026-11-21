# UI Stage 4 — Career Studios redesign

**Scope:** Refresh the Career Studios learner experience while retaining the existing interview session and feedback engine.

## Implemented

- [x] Reframe Career as a dedicated local practice workspace with a clear purpose and privacy/local-use cues.
- [x] Give the three authored studios distinct, responsive cards with category, duration, main-question count, skill context, and clear selection actions.
- [x] Add a calm session setup with practice-style choice and supportive expectations.
- [x] Reorganise the active interview into interviewer prompt and learner response areas.
- [x] Add accessible main-question progress, including explicit follow-up context; follow-ups do not falsely advance the main-question count.
- [x] Clarify optional voice, editable transcript, and unsaved answer draft state.
- [x] Restructure completion/review and recent-session history while preserving existing feedback, evidence, comparison, memory save, plan handoff, retry, resume, and delete actions.
- [x] Use the approved warm, professional-playful palette, responsive card layouts, original mascot art, visible focus, and reduced-motion support.
- [x] Add browser regression coverage for studio cards, local-use cues, accessible progress and draft state.

## Manual acceptance

- [ ] Visually review Career at desktop and narrow/mobile widths; no overflow or clipped controls.
- [ ] Keyboard through studio selection, setup, prompt hints, voice controls, response, review and history; confirm focus visibility.
- [ ] Screen-reader check for studio headings, prompt/follow-up context, progress value, recording/transcription status, draft state, and feedback.
- [ ] Complete a full Project Explanation, HR/Behavioural, and Technical Fundamentals session using text.
- [ ] Confirm follow-up progression and resume of an in-progress session.
- [ ] Confirm optional microphone/STT/TTS paths, transcript editing and cancellation remain intact.
- [ ] Confirm review, previous-attempt comparison, learner-approved memory save, add-to-plan, retry, history open/delete all work.
- [ ] Confirm no new remote service, API, database schema, curriculum change, or required dependency.

**Status:** implementation and automated regression added; target-device visual/audio/accessibility acceptance remains open.
