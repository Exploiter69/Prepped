# ADR-003: Optional Groq Whisper Turbo transcription

**Status:** Implemented; real account/device acceptance pending
**Date:** 2026-11-19
**Supersedes:** The no-remote-STT restriction in ADR-002 only when the user explicitly configures `GROQ_API_KEY`.

## Context

The Vosk small English model produced materially inaccurate transcripts during a real learner recording. This blocks a credible voice-first demonstration. The existing STT protocol allows a provider change without rewriting the browser, session controller, database, or feedback flow.

Constraints remain: no paid dependency, no mandatory API credential, no provider key in browser code, no raw-audio persistence by Prepped, and a text fallback.

## Decision

- Add an optional `GroqWhisperSTT` adapter using `whisper-large-v3` and Groq's OpenAI-compatible `/audio/transcriptions` endpoint.
- Select it only when the server process has `GROQ_API_KEY`; otherwise select local Vosk.
- Convert the existing in-memory mono 16 kHz PCM to WAV in memory and send it to Groq. No audio file is written by Prepped.
- Keep the transcript editable and submit corrected text through the existing session endpoint.
- Keep the API key server-side. Never expose it to JavaScript, HTML, logs, or the repository.
- Map authentication, rate-limit, timeout, and provider failures to clear user-facing errors. Do not silently fall back to a potentially poor Vosk transcript after a configured cloud-provider failure.
- Keep text mode available at all times.

## Cost and data handling

Groq publishes free-tier rate limits and separate per-hour pricing for paid usage. This project uses only the free access available to the account and does not require or recommend upgrading to a paid plan. Free quotas and model availability can change; a rate-limit response must be handled gracefully.

Groq states that inference inputs/outputs are not retained by default, but may be temporarily logged for reliability or abuse monitoring for up to 30 days. Its Data Controls page offers Zero Data Retention. Users must review current settings and provider terms before sending real recordings. Audio is sent to Groq only after the developer deliberately configures the API key.

## Consequences

- Better transcription quality is expected from a multilingual Whisper Large model, but it is not yet measured on this project's target speakers.
- The application has optional remote STT and TTS when configured; local Vosk and Piper/espeak remain available without credentials or internet.
- The app's privacy statement reflects both active STT and TTS providers. Prompt synthesis is cached to reduce repeat latency and metered calls.
- Provider outage, network failure, invalid key, or free-tier exhaustion must not prevent typed practice.

## Acceptance gates

1. Confirm the selected engine is `groq-whisper` in `/api/voice/status` after configuration.
2. Record and transcribe a clear 20–40 second Indian English answer.
3. Check technical terms and names; compare against what was actually spoken.
4. Edit the transcript and submit it through the existing practice flow.
5. Confirm no audio file is written locally and the API key is not present in frontend assets.
6. Confirm a 429/provider failure leaves text input usable.
7. Do not claim validated accuracy until several consented representative recordings are evaluated against human reference transcripts.

## References

- [Groq speech-to-text API](https://console.groq.com/docs/speech-to-text)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [Groq data handling](https://console.groq.com/docs/your-data)
- [ADR-002: local record/stop voice slice](ADR-002-LOCAL-VOICE-SLICE.md)


## TTS extension (2026-11-21)

- Groq Orpheus English uses `canopylabs/orpheus-v1-english` via `POST /audio/speech`, voice `troy`, WAV response. The documented input limit is 200 characters; longer prompts use local TTS.
- Groq is selected for both STT and TTS only when the server environment contains `GROQ_API_KEY` and the HTTP dependency is available. The key is never sent to the browser.
- Remote TTS failure/quota/short-input constraints fall back to installed local Piper or espeak-ng. Generated WAVs are cached in a bounded process-memory LRU and up to four small prompt blobs in the browser.
- TTS is metered by provider; users should check current pricing/limits and avoid enabling it for data they do not wish to send.
- References: [Groq TTS](https://console.groq.com/docs/text-to-speech/) · [Orpheus](https://console.groq.com/docs/text-to-speech/orpheus)
