"""Application-level voice service combining local STT, TTS, and audio rules."""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prepped.voice.audio import decode_audio_to_pcm
from prepped.voice.base import SpeechToTextEngine, TextToSpeechEngine
from prepped.voice.errors import (
    AudioTooLarge,
    InvalidAudio,
    InvalidSpeechText,
    VoiceUnavailable,
)
from prepped.voice.stt import GroqWhisperSTT, VoskSTT
from prepped.voice.tts import EspeakTTS, PiperTTS


ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class VoiceSettings:
    """Bounds for local voice work; all are intentionally modest."""

    max_audio_bytes: int = 12 * 1024 * 1024
    max_recording_seconds: int = 60
    max_tts_characters: int = 1_200


AudioDecoder = Callable[..., bytes]


class VoiceService:
    """Coordinates local engines while keeping the HTTP layer thin."""

    def __init__(
        self,
        stt: SpeechToTextEngine,
        tts: TextToSpeechEngine,
        *,
        decoder: AudioDecoder = decode_audio_to_pcm,
        settings: VoiceSettings | None = None,
    ) -> None:
        self.stt = stt
        self.tts = tts
        self.decoder = decoder
        self.settings = settings or VoiceSettings()

    def status(self) -> dict[str, Any]:
        stt_status = self.stt.status()
        tts_status = self.tts.status()
        return {
            "stt": stt_status.as_dict(),
            "tts": tts_status.as_dict(),
            "limits": {
                "max_recording_seconds": self.settings.max_recording_seconds,
                "max_audio_bytes": self.settings.max_audio_bytes,
                "max_tts_characters": self.settings.max_tts_characters,
            },
            "privacy": (
                "Recorded audio is sent to Groq for transcription; Prepped does not save raw audio locally. "
                "Use only practice recordings you are comfortable sending to the provider."
                if getattr(self.stt, "remote", False)
                else "Recordings are decoded and transcribed in memory on this computer. "
                "Prepped does not save raw audio or send it to a remote provider."
            ),
            "fallback": "Text input remains available if recording or transcription fails.",
        }

    def transcribe(self, audio_bytes: bytes, content_type: str = "") -> dict[str, Any]:
        if not audio_bytes:
            raise InvalidAudio("No audio was received. Record an answer or type it instead.")
        if len(audio_bytes) > self.settings.max_audio_bytes:
            raise AudioTooLarge(
                "The recording is too long to transcribe. Keep it under "
                f"{self.settings.max_recording_seconds} seconds or type your answer."
            )

        stt_status = self.stt.status()
        if not stt_status.available:
            raise VoiceUnavailable(stt_status.detail)

        # Content type is accepted for diagnostics/adapters; ffmpeg detects the
        # container itself. Nothing is written to disk.
        del content_type
        pcm = self.decoder(
            audio_bytes,
            max_seconds=self.settings.max_recording_seconds,
        )
        text = self.stt.transcribe(pcm)
        engine = self.stt.status()
        return {
            "text": text,
            "engine": engine.engine,
            "model": engine.model,
            "audio_bytes": len(audio_bytes),
            "stored_audio": False,
        }

    def synthesize(self, text: str) -> bytes:
        clean = " ".join(text.split())
        if not clean:
            raise InvalidSpeechText("No question text was provided to speak.")
        if len(clean) > self.settings.max_tts_characters:
            raise InvalidSpeechText("The question is too long to speak locally.")
        tts_status = self.tts.status()
        if not tts_status.available:
            raise VoiceUnavailable(tts_status.detail)
        return self.tts.synthesize(clean)


def build_voice_service(root: Path = ROOT) -> VoiceService:
    """Build the default local stack without downloading or loading models.

    Environment overrides let another local engine/model be selected without
    changing application code.
    """
    stt_model = Path(
        os.environ.get(
            "PREPPED_STT_MODEL_DIR",
            root / "models" / "vosk-model-small-en-us-0.15",
        )
    )
    piper_model = Path(
        os.environ.get(
            "PREPPED_PIPER_MODEL",
            root / "models" / "piper" / "en_US-lessac-medium.onnx",
        )
    )

    piper = PiperTTS(piper_model)
    espeak = EspeakTTS(os.environ.get("PREPPED_ESPEAK_BIN"))
    # Prefer the better local voice, but never require it: espeak-ng keeps
    # spoken prompts working on a machine without the optional Piper model.
    tts: TextToSpeechEngine = piper if piper.status().available else espeak
    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_api_key:
        stt: SpeechToTextEngine = GroqWhisperSTT(groq_api_key)
    else:
        stt = VoskSTT(stt_model)
    return VoiceService(stt, tts)
