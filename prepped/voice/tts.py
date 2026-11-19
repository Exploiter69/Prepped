"""Local text-to-speech engines.

Piper is preferred when its optional package and voice model are installed.
espeak-ng is the tiny fallback already available on many Linux systems. Both
run as local processes; no text is sent to a remote provider.
"""
from __future__ import annotations

import importlib.util
import io
import shutil
import subprocess
import threading
import wave
from pathlib import Path

from prepped.voice.base import EngineStatus, TextToSpeechEngine
from prepped.voice.errors import TextToSpeechError, VoiceUnavailable


class PiperTTS(TextToSpeechEngine):
    """Piper neural TTS using a local ONNX voice model."""

    name = "piper"

    def __init__(self, model_path: Path) -> None:
        self.model_path = Path(model_path)
        self._voice = None
        self._load_lock = threading.Lock()
        self._synth_lock = threading.Lock()

    def status(self) -> EngineStatus:
        if importlib.util.find_spec("piper") is None:
            return EngineStatus(
                kind="tts",
                engine=self.name,
                available=False,
                model=self.model_path.name,
                detail=(
                    "Optional Piper TTS is not installed. Install piper-tts and a voice model "
                    "for a more natural local voice; espeak-ng may be used instead."
                ),
            )
        if not self.model_path.is_file():
            return EngineStatus(
                kind="tts",
                engine=self.name,
                available=False,
                model=self.model_path.name,
                detail=(
                    "Piper is installed but its voice model is missing. Run "
                    "python -m piper.download_voices --data-dir models/piper en_US-lessac-medium "
                    "or use espeak-ng."
                ),
            )
        return EngineStatus(
            kind="tts",
            engine=self.name,
            available=True,
            model=self.model_path.name,
            detail="Local Piper text-to-speech voice is installed.",
        )

    def _load_voice(self):
        with self._load_lock:
            if self._voice is None:
                try:
                    from piper import PiperVoice
                except ImportError as exc:  # pragma: no cover - status covers this
                    raise VoiceUnavailable(
                        "Piper TTS is not installed. Read the question on screen or use espeak-ng."
                    ) from exc
                try:
                    self._voice = PiperVoice.load(str(self.model_path))
                except Exception as exc:
                    raise TextToSpeechError(
                        "The local Piper voice could not be loaded. Read the question on screen instead."
                    ) from exc
            return self._voice

    def synthesize(self, text: str) -> bytes:
        voice = self._load_voice()
        buffer = io.BytesIO()
        try:
            with self._synth_lock:
                with wave.open(buffer, "wb") as wav_file:
                    voice.synthesize_wav(text, wav_file)
        except Exception as exc:
            raise TextToSpeechError(
                "Local spoken prompts failed. Read the question on screen instead."
            ) from exc
        audio = buffer.getvalue()
        if not audio:
            raise TextToSpeechError("Local spoken prompts returned no audio. Read the question on screen.")
        return audio


class EspeakTTS(TextToSpeechEngine):
    """Small formant-synthesis fallback using an installed espeak-ng binary."""

    name = "espeak-ng"

    def __init__(self, binary: str | None = None) -> None:
        self.binary = binary or shutil.which("espeak-ng") or shutil.which("espeak")

    def status(self) -> EngineStatus:
        if not self.binary:
            return EngineStatus(
                kind="tts",
                engine=self.name,
                available=False,
                detail=(
                    "No local text-to-speech engine was found. Read the question on screen, "
                    "or install espeak-ng/Piper for spoken prompts."
                ),
            )
        return EngineStatus(
            kind="tts",
            engine=self.name,
            available=True,
            model=Path(self.binary).name,
            detail="Local espeak-ng text-to-speech is available.",
        )

    def synthesize(self, text: str) -> bytes:
        if not self.binary:
            raise VoiceUnavailable(
                "No local text-to-speech engine is installed. Read the question on screen."
            )
        try:
            result = subprocess.run(
                [self.binary, "-v", "en-us", "-s", "150", "-p", "45", "--stdout"],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TextToSpeechError(
                "Local spoken prompts failed. Read the question on screen instead."
            ) from exc
        if result.returncode != 0 or not result.stdout:
            raise TextToSpeechError(
                "Local spoken prompts failed. Read the question on screen instead."
            )
        return result.stdout
