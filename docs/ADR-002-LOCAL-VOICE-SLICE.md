# ADR-002: Local record/stop voice slice

**Status:** Accepted and implemented for the first voice milestone<br>
**Date:** 2026-11-04<br>
**Decision owners:** Prepped project team<br>
**Scope:** Local speech-to-text, local interviewer prompt playback, and editable transcripts in the existing project-interview scenario<br>
**Supersedes:** None. Amends the voice exclusions in ADR-001.

## Context

Prepped's product direction is now voice-first: Indian engineering students practising placement interviews, professional communication, English fluency, and technical conversations. The existing text MVP is still useful, but it is frozen for feature development except material bugs.

The first voice milestone must work on the target development machine:

- Intel i5-1235U, Intel UHD graphics, approximately 7.5 GiB RAM.
- Linux/Omarchy/Arch, Python virtual environment.
- No CUDA assumption.
- ₹0 mandatory spend.
- No paid APIs, cloud AI, subscriptions, paid hosting, or usage-based services.
- No voice or answer content sent to a remote provider.
- No raw audio persistence by default.
- Existing FastAPI + plain HTML/CSS/JS + SQLite stack.
- Text mode must remain fully functional.
- STT/TTS engines must be replaceable later.

This ADR covers the smallest real slice: record/stop, local transcription, editable transcript, submit through the existing session backend, local spoken prompts, and explicit failure fallback. It does not cover realtime streaming, always-listening agents, LLM feedback, or pronunciation scoring.

## Options considered

| Option | Assessment |
|---|---|
| **Vosk + small English model** | **Chosen for STT.** Apache 2.0, pip wheel, CPU-friendly, 40 MB compressed / 68 MB on disk, no cloud account. Accuracy is not validated for Indian English; the transcript is editable. |
| whisper.cpp | Plausible future adapter. MIT code, small models, CPU-capable, but requires a native build and more model/setup handling. Not necessary for the first slice. |
| faster-whisper | Strong accuracy option, but adds a heavier inference stack and was not needed to prove the local record/transcribe flow. |
| Cloud STT | Rejected: violates zero-mandatory-spend and no-remote-voice-content constraints. |
| **Piper** | **Chosen for TTS when available.** Local neural TTS, CPU-compatible, 61 MB medium voice. Current pip package is GPL-3.0-or-later; optional and invoked locally. |
| **espeak-ng** | **Chosen as TTS fallback.** Tiny, already available on many Linux systems, fully local, robotic but functional. GPL-3.0. |
| Browser speech synthesis | Rejected as the primary path because voice/engine availability is inconsistent and less inspectable than a local server adapter. |
| LiveKit/Pipecat/realtime frameworks | Rejected for this milestone: unnecessary orchestration for record/stop turns. |

Licensing and model availability were checked on 2026-11-04. Do not treat those dates as permanent; re-verify before redistribution or public deployment.

## Decision

Use a small local voice layer with narrow adapters:

1. **Browser capture:** `MediaRecorder` with explicit **Start recording** / **Stop recording**. No always-listening mode.
2. **Transport:** the browser posts the raw recording blob to `POST /api/voice/transcribe`. No multipart dependency is required.
3. **Decoding:** local `ffmpeg` reads the container from stdin and writes mono 16 kHz signed 16-bit PCM to stdout. No temporary raw-audio file is created.
4. **STT:** `VoskSTT` wraps a local Vosk model directory. The model is loaded lazily and never downloaded at startup.
5. **Transcript:** the result is returned as JSON and inserted into the existing editable answer textarea. The learner must be able to correct errors before submission.
6. **Submission:** the corrected text uses the existing `POST /api/sessions/{id}/answers` endpoint. The session backend does not know or care that the text originated from speech.
7. **TTS:** `PiperTTS` returns WAV bytes from a local model; `EspeakTTS` is the fallback. The browser provides **Play**, **Stop**, and **Replay**.
8. **Failure handling:** missing package/model, missing `ffmpeg`, denied microphone, empty/silent/undecodable audio, oversized upload, and TTS failure all return clear messages and leave text mode usable.
9. **Privacy:** no raw audio persistence. Only the corrected answer text is stored by the existing SQLite session store.

## Module boundaries

```text
static/voice.js                 Browser recording, transcript insertion, TTS controls
        │
        ▼
prepped/voice/routes.py         HTTP contract and safe error mapping
        │
        ▼
prepped/voice/service.py        Limits, availability, engine coordination
        ├── prepped/voice/audio.py   ffmpeg decode to PCM, in memory
        ├── prepped/voice/stt.py     VoskSTT (replaceable)
        └── prepped/voice/tts.py     PiperTTS / EspeakTTS (replaceable)
        │
        ▼
existing sessions/answers/feedback backend (unchanged)
```

The text feedback engine is not modified by this ADR. The voice layer does not add LLM feedback, adaptive intelligence, or phrase heuristics.

## API contract

- `GET /api/voice/status` — availability of STT/TTS, model names, limits, privacy/fallback text.
- `POST /api/voice/transcribe` — raw audio request body; JSON response with `text`, `engine`, `model`, `audio_bytes`, `stored_audio: false`.
- `POST /api/voice/tts` — JSON `{ "text": "..." }`; local WAV response with `Cache-Control: no-store`.

Limits:

- Recording: 60 seconds in the browser and 60 seconds decoded server-side.
- Upload: 12 MiB.
- TTS text: 1,200 characters.
- Answer text: existing 6,000-character limit.

## Consequences

### Positive

- The first voice milestone is real and end-to-end, not a mock.
- Text mode remains the reliable fallback.
- STT/TTS engines are replaceable without changing the session backend.
- No mandatory paid service or remote voice provider.
- No raw audio storage by default.
- The implementation is small enough for a student team to understand and test.

### Trade-offs and limitations

- Vosk small English accuracy on Indian English is **not validated**. A single synthetic test produced an imperfect transcript. Editing is essential.
- Speech accuracy, TTS quality, and latency have not been benchmarked across devices or repeated runs.
- Piper's first load is noticeably slower than subsequent synthesis on the development laptop; no benchmark claim is made.
- No streaming, VAD, interruption, always-listening, pronunciation scoring, or LLM feedback.
- `espeak-ng` is functional but robotic.
- The browser microphone flow still needs a human acceptance check on the target machine.
- The current Python environment is 3.14; CI uses 3.11. The optional Vosk wheel is platform-independent Python and was verified locally, but CI does not install the voice extras.

## Revisit conditions

Reopen this decision when:

- A measured accuracy or latency problem on real Indian English speech justifies a different local STT engine.
- The target hardware cannot run the chosen models acceptably.
- A local TTS voice is clearly better while staying zero-mandatory-cost.
- Real user validation shows that record/stop is insufficient and a different interaction is justified.
- Licensing changes affect redistribution.

Any replacement must keep the adapter boundary, text fallback, no-remote-audio rule, no-default-raw-audio-persistence rule, and the existing session backend.

## Related documents

- [Voice setup and privacy](VOICE.md)
- [Current state](CURRENT_STATE.md)
- [Complete roadmap](COMPLETE_ROADMAP.md)
- [ADR-001: text architecture](ADR-001-MINIMAL-LOCAL-FIRST-ARCHITECTURE.md)
