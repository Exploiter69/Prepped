"""Decode browser recordings to mono 16 kHz PCM without persisting audio."""
from __future__ import annotations

import shutil
import subprocess

from prepped.voice.errors import InvalidAudio, NoSpeechDetected, VoiceUnavailable


SAMPLE_RATE = 16_000
MIN_PCM_BYTES = SAMPLE_RATE * 2 // 2  # 0.5 seconds of 16-bit mono audio


def decode_audio_to_pcm(
    audio_bytes: bytes,
    *,
    max_seconds: int = 60,
    timeout_seconds: int = 90,
) -> bytes:
    """Decode an in-memory browser recording to raw 16-bit mono PCM.

    ffmpeg reads the uploaded container from stdin and writes raw PCM to
    stdout, so the recording never needs a temporary file or database row.
    """
    if not audio_bytes:
        raise InvalidAudio("No audio was received. Record an answer or type it instead.")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise VoiceUnavailable(
            "ffmpeg is required to read browser recordings but was not found. "
            "Install ffmpeg or type your answer instead."
        )

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-t", str(max_seconds),
        "-map_metadata", "-1",
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "pipe:1",
    ]
    try:
        result = subprocess.run(
            command,
            input=audio_bytes,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise InvalidAudio(
            "Reading the recording took too long. Try a shorter recording or type your answer instead."
        ) from exc
    except OSError as exc:
        raise VoiceUnavailable(
            "The local audio decoder could not start. Install ffmpeg or type your answer instead."
        ) from exc

    if result.returncode != 0:
        # Decoder diagnostics can contain user-controlled container metadata.
        # Keep those details out of API responses and logs.
        raise InvalidAudio(
            "The browser recording could not be decoded. Try recording again or type your answer instead."
        )

    pcm = result.stdout
    if len(pcm) < MIN_PCM_BYTES:
        raise NoSpeechDetected(
            "The recording was too short or silent. Try again with a slightly longer answer or type it instead."
        )
    return pcm
