# UI Stage 3 — Practice Room redesign

**Scope:** Redesign the Project Explanation practice journey without changing the practice API, SQLite schema, curriculum, voice providers, or single-user local architecture.

## Implemented

- [x] Give the active prompt a clear hierarchy and persistent question number.
- [x] Expose answered-question progress as an accessible progress bar with current values and text.
- [x] Keep spoken prompt play, stop, and replay controls beside the prompt.
- [x] Make microphone recording an optional response path and keep editable text entry available at all times.
- [x] Add a live-only microphone waveform visualizer using the browser Web Audio analyser where supported; fall back to a CSS activity animation when unavailable.
- [x] Add a recording elapsed/limit clock.
- [x] Distinguish an unsaved draft from a saved answer and mark inserted transcripts as editable.
- [x] Keep privacy/provider handling visible in an expandable disclosure.
- [x] Improve review screen hierarchy while retaining question notes, transparent checklist, attempt comparison, explicit memory handoff, retry, history and deletion.
- [x] Respect narrow layouts, keyboard focus styles and reduced-motion preferences.
- [x] Preserve microphone permission handling, late-grant cleanup, cancellation on navigation, abortable transcription/TTS, stream release, and raw-audio non-persistence.
- [x] Add Chromium browser coverage for accessible progress, draft state, text fallback, and recording visualizer activation/cleanup.

## Manual acceptance — target Omarchy laptop

- [ ] Desktop: prompt, voice controls, waveform, transcript and actions fit without horizontal scrolling.
- [ ] Mobile/narrow viewport: controls wrap cleanly; textarea remains usable; no clipped action buttons.
- [ ] Keyboard-only: tab through prompt playback, record/stop, answer, skip/save/end; focus remains visible.
- [ ] Screen reader: prompt, progress value, recording/transcription status, draft state and privacy disclosure are announced meaningfully.
- [ ] Microphone denied: clear recovery message; typed response remains usable.
- [ ] Microphone granted: waveform responds to voice; timer advances; stop releases microphone.
- [ ] Transcription completes: transcript is inserted as an editable draft; user can correct it before saving.
- [ ] Navigate away during permission/transcription: pending work is invalidated and microphone tracks are stopped.
- [ ] Groq path, if configured: disclosure clearly states audio is sent to Groq before capture; no silent remote fallback.
- [ ] Local Vosk path: transcription remains local.
- [ ] TTS: play, stop, replay and navigation cleanup work where the local engine is installed.
- [ ] Offline text-only completion works without microphone, STT, or TTS.
- [ ] Review, memory handoff, retry/comparison, history and delete remain functional.

## Boundaries

The waveform is a transient browser visualisation of the current microphone stream, not an audio recording or quality meter. It does not measure pronunciation, volume quality, accent, confidence, or speaking ability. Transcription remains an editable draft and may contain recognition errors. Feedback remains a formative text checklist, not a grade or hiring prediction.

**Status:** implementation added; automated CI and target-device manual acceptance pending.
