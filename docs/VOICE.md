# Prepped — Local Voice Setup, Privacy, and Troubleshooting

**Updated:** 2026-11-20<br>
**Scope:** Push-to-talk recording, editable transcription, prompt playback, and cancellation across Project Practice, Learning, and Career studios.<br>
**Architecture decisions:** [ADR-002](ADR-002-LOCAL-VOICE-SLICE.md) · [ADR-003](ADR-003-GROQ-WHISPER-TRANSCRIPTION.md)

## What is implemented

- Browser microphone recording with **Start recording** and **Stop recording**.
- Local speech-to-text with Vosk, or optional Groq Whisper transcription when `GROQ_API_KEY` is configured.
- Editable transcript before submission through the existing answer endpoint.
- Local spoken interviewer prompts with Piper, falling back to `espeak-ng`.
- **Play question aloud**, **Stop**, and **Replay** controls.
- Clear errors and a text-only fallback.
- No raw audio persistence by Prepped. Groq mode explicitly sends audio to Groq; Vosk mode stays local.
- In-flight prompt synthesis and transcription browser requests are abortable when the prompt/workspace changes or the learner leaves; stale responses are ignored.
- Career studios use authored contextual follow-ups selected by narrow, documented text cues, with a visible explanation when a cue selects the prompt. Learners can reveal an authored hint or switch to simpler wording without losing the original prompt; the chosen variant is retained with the answer.
- Career review provides one possible answer-specific next action, explicitly framed as heuristic formative guidance rather than correctness feedback.
- Learners may explicitly save an answer or coaching action to existing Memory, or add a future studio practice to the existing daily plan.
- A retry review can compare previous and current answers side by side. Differences are for learner reflection only, not an automated improvement measure.

Voice remains push-to-talk and turn-based. There is no always-listening mode, streaming transcript, voice activity detection, full-duplex conversation, or model-generated coaching. Context selection and coaching are deterministic lexical heuristics; they can miss equivalent wording and can match weak answers. They do not assess technical correctness, proficiency, accent, pronunciation quality, emotion, personality, hiring suitability, or placement readiness.

## Shared voice interaction contract

The Learning/Project Practice and Career workspaces keep their existing controllers, but follow the same user-visible lifecycle:

| Stage | Behaviour | Cancellation/recovery |
|---|---|---|
| Idle | Text input is ready; recording and prompt playback require a learner action | No microphone is active |
| Requesting permission | The browser asks for microphone access only after the learner presses Record | Leaving the workspace invalidates the request; a late stream is stopped immediately |
| Recording | A visible status is shown and the capture duration is bounded | Stop finishes the recording; Cancel/navigation discards it and releases tracks |
| Transcribing | The selected STT adapter processes the in-memory recording | Cancel/navigation aborts the browser request; stale results cannot update another prompt |
| Transcript ready | Recognised text is inserted into an editable answer field | The learner edits the text before submitting; the field remains bounded to 6,000 characters |
| Failed / no speech | A specific recovery message is shown | Retry recording or continue with text; no automatic remote-provider fallback |
| Preparing / playing prompt | The visible prompt remains readable while local TTS is requested or played | Stop, prompt change, navigation, and page unload abort pending synthesis, stop playback, and release the object URL |

A normal learner-initiated Stop is not a cancellation: it allows transcription to finish while the same prompt remains active. A navigation or Cancel action is a cancellation: it aborts the request, invalidates its generation, stops media tracks, and ignores any late callback. A failed voice path never blocks the text path.

Career prompts additionally expose authored simpler wording and a prompt hint. The selected wording is stored with the submitted answer. Retry comparisons show the prior and current text but do not calculate or claim improvement.

## One-time installation

Nothing in this section runs automatically when the app starts.

### System tools

On Arch/Omarchy:

```bash
sudo pacman -S ffmpeg espeak-ng
```

`ffmpeg` is required to decode browser recordings. `espeak-ng` is the zero-download TTS fallback. Text mode works without either.

### Models and Python extras

From the repository root, with the project virtual environment activated:

```bash
./scripts/setup_voice.sh
```

The script uses `.venv/bin/python` when that virtual environment exists, so it also avoids the system Python's PEP 668 restriction. Set `PYTHON=/path/to/python` to override.

This explicitly:

1. Installs the `voice` and `voice-piper` Python extras.
2. Downloads the Vosk small English model (about 40 MB compressed, 68 MB on disk) into `models/vosk-model-small-en-us-0.15/`.
3. Downloads the Piper `en_US-lessac-medium` voice (about 61 MB) into `models/piper/`.

For speech-to-text only:

```bash
./scripts/setup_voice.sh --stt-only
```

Then spoken prompts use `espeak-ng` if installed.

### Manual alternative

```bash
python -m pip install -e ".[voice,voice-piper]"

# Vosk small English model
curl -fL -o /tmp/vosk-model.zip \
  https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
python -c 'import zipfile; zipfile.ZipFile("/tmp/vosk-model.zip").extractall("models")'

# Optional Piper voice
mkdir -p models/piper
python -m piper.download_voices --data-dir models/piper en_US-lessac-medium
```

Models are ignored by Git and must not be committed.

## Model and engine choices

| Role | Default | Fallback | License | Approximate local size |
|---|---|---|---|---|
| STT | Vosk 0.3.45 + `vosk-model-small-en-us-0.15` | None; text mode remains | Apache 2.0 | 40 MB download / 68 MB disk |
| TTS | Piper 1.8.0 + `en_US-lessac-medium` | `espeak-ng` | Piper: GPL-3.0-or-later; espeak-ng: GPL-3.0 | 34 MB package + 61 MB voice; espeak-ng tiny |
| Decode | `ffmpeg` | None; text mode remains | Build-dependent (LGPL/GPL) | System package |

Vosk remains the offline fallback: it runs on CPU and needs no cloud account, but the small English model is not reliable enough for every Indian English accent. For the demo, an optional Groq Whisper adapter is available. It uses `whisper-large-v3` through Groq's OpenAI-compatible transcription endpoint. It is selected only when `GROQ_API_KEY` is set; otherwise Vosk remains selected.

Why Piper first for TTS: it produces more natural speech than `espeak-ng`, runs locally on CPU, and worked on the target machine. `espeak-ng` keeps prompts working when Piper or its model is absent.

### Environment overrides

```bash
export GROQ_API_KEY="your-groq-api-key"  # optional; selects Groq Whisper
export PREPPED_STT_MODEL_DIR=/path/to/vosk-model
export PREPPED_PIPER_MODEL=/path/to/voice.onnx
export PREPPED_ESPEAK_BIN=/path/to/espeak-ng
```

If the Piper package or model is unavailable, Prepped automatically uses `espeak-ng` when present. If no TTS is available, the question text remains visible and the UI explains the fallback.

## How audio flows

```text
Browser MediaRecorder
        │  raw blob in POST body (not multipart)
        ▼
POST /api/voice/transcribe
        │
        ▼
ffmpeg: stdin → mono 16 kHz PCM → stdout
        │  (no temporary audio file)
        ▼
Groq Whisper (if configured) or Vosk offline recogniser
        │
        ▼
JSON transcript  →  editable answer textarea
        │
        ▼
Existing POST /api/sessions/{id}/answers
```

TTS flows in the opposite direction: the browser sends only the question text to `POST /api/voice/tts`; the local engine returns a WAV. The audio element supports stop/replay.

## Privacy rules

- **No raw audio persistence by default.** The recording is read from the request body, decoded in memory, and discarded after transcription.
- No audio is written to SQLite. Only the learner's corrected answer text is saved by the existing session store.
- Vosk mode sends no voice content to a remote provider. Groq mode sends the recording to Groq for transcription; the API key remains server-side.
- Groq says inference inputs/outputs are not retained by default, but may be temporarily logged for reliability or abuse investigations for up to 30 days. Global Zero Data Retention can be enabled in Groq Data Controls. Review current provider terms and settings before using real personal recordings.
- No model training on learner data.
- Model files are local and ignored by Git.
- Do not record other people or confidential interview content into the prototype.
- History deletion removes saved sessions and answers; it does not need to remove audio because audio is not stored.

## API limits

- Recording cap: 60 seconds in the browser and 60 seconds of decoded audio on the server.
- Upload cap: 12 MiB.
- TTS text cap: 1,200 characters.
- Transcript text is subject to the existing 6,000-character answer limit.
- Transcription is serialised on the local app to keep CPU/memory predictable.

## Troubleshooting

### “Local speech-to-text model not found”

Run:

```bash
./scripts/setup_voice.sh
```

Then restart the server. The app does not download models at startup.

### “Groq transcription dependency missing”

```bash
python -m pip install -e ".[voice-cloud]"
```

### “Groq rejected the API key”

Check that `GROQ_API_KEY` is set in the same terminal that starts Uvicorn, then restart the server. Never put the key in `static/` JavaScript or commit it.

### “The Vosk Python package is not installed”

Activate the project virtual environment and run:

```bash
python -m pip install -e ".[voice]"
```

### “ffmpeg is required to read browser recordings”

```bash
sudo pacman -S ffmpeg
```

Text mode still works without it.

### Microphone permission denied

Allow microphone access for `http://127.0.0.1:8000` in the browser site settings, then reload. If the browser cannot record, type the answer instead. `getUserMedia` requires a secure context; localhost/127.0.0.1 is treated as secure by common browsers.

### No speech detected or the transcript is wrong

- Record closer to the microphone, reduce background noise, and speak a little longer.
- Local Vosk can misrecognise words, especially names, technical terms, and Indian English accents. Configure Groq Whisper for the demo if you have a free-tier key.
- Edit the transcript before saving. Accuracy has **not** been validated.
- Try a different local model directory with `PREPPED_STT_MODEL_DIR` if you have one installed.

### Spoken prompts do not play

Check `/api/voice/status`. If Piper is unavailable, install `espeak-ng` or rerun setup. The question is always visible as text.

### The first spoken prompt is slow

Piper loads its voice model on first use. This one-time load was about 4.5 seconds on the development laptop. Timing has not been benchmarked across devices.

## Manual browser acceptance checklist

These steps still need a human on a machine with a microphone:

- [ ] Open `http://127.0.0.1:8000` and confirm the browser offers text and voice.
- [ ] Press **Play question aloud**; confirm local speech starts.
- [ ] Press **Stop**; confirm speech stops.
- [ ] Press **Replay**; confirm the question plays again.
- [ ] Press **Start recording**; allow microphone permission; confirm a recording timer appears.
- [ ] Press **Stop recording**; confirm a transcript appears in the answer box.
- [ ] Edit a recognition error and save; confirm the corrected text reaches feedback through the existing backend.
- [ ] Deny microphone permission; confirm a clear error and working text fallback.
- [ ] Temporarily point `PREPPED_STT_MODEL_DIR` at a missing directory; confirm a clear model error and working text fallback.
- [ ] Confirm no raw audio file is created in the repository or data directory.

Automated tests cover the API boundaries, failure paths, text fallback, and a synthetic real-model integration check. They do not replace the browser/microphone check above.

## Replacing an engine

Implement the small protocol in `prepped/voice/base.py`:

```python
class SpeechToTextEngine(Protocol):
    name: str
    def status(self) -> EngineStatus: ...
    def transcribe(self, pcm: bytes) -> str: ...

class TextToSpeechEngine(Protocol):
    name: str
    def status(self) -> EngineStatus: ...
    def synthesize(self, text: str) -> bytes: ...
```

Then select it in `build_voice_service()` in `prepped/voice/service.py`. Keep the HTTP contract and existing session backend unchanged. Any remote provider must be explicitly opt-in, disclose that audio leaves the device, keep credentials server-side, and never persist raw audio in Prepped.

## Current limitations

- Speech recognition accuracy is not validated on real Indian English speech, including with Groq Whisper.
- A single synthetic Vosk transcript was imperfect; this is expected and is why editing is mandatory.
- No streaming, partial transcripts, VAD, interruption, or always-listening.
- No pronunciation or delivery scoring.
- No LLM feedback or adaptive personalisation in this phase.
- TTS and STT latency/memory need repeatable measurement before claims are made.
- The browser microphone flow is not verified by the automated test suite in this headless development session.
