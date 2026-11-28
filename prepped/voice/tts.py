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

    def synthesize(self, text: str, *, speed: float = 1.0) -> bytes:
        voice = self._load_voice()
        clamped = max(0.7, min(1.5, float(speed or 1.0)))
        length_scale = round(1.0 / clamped, 3)
        buffer = io.BytesIO()
        try:
            with self._synth_lock:
                with wave.open(buffer, "wb") as wav_file:
                    if abs(clamped - 1.0) > 0.01:
                        try:
                            from piper.config import SynthesisConfig  # type: ignore
                            voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=length_scale))
                        except (ImportError, TypeError):
                            try:
                                voice.synthesize_wav(text, wav_file, length_scale=length_scale)
                            except TypeError:
                                voice.synthesize_wav(text, wav_file)
                    else:
                        voice.synthesize_wav(text, wav_file)
        except Exception as exc:
            raise TextToSpeechError(
                "Local spoken prompts failed. Read the question on screen instead."
            ) from exc
        audio = buffer.getvalue()
        if not audio:
            raise TextToSpeechError("Local spoken prompts returned no audio. Read the question on screen.")
        return audio


class GroqOrpheusTTS(TextToSpeechEngine):
    """Remote low-latency English TTS via Groq Orpheus; key remains server-side."""

    name = "groq-orpheus"
    remote = True
    endpoint = "https://api.groq.com/openai/v1/audio/speech"
    model_name = "canopylabs/orpheus-v1-english"
    voice_name = "troy"
    max_characters = 200  # Orpheus model input limit documented by Groq.

    def __init__(self, api_key: str, *, timeout_seconds: float = 35.0) -> None:
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds

    def status(self) -> EngineStatus:
        if not self.api_key:
            return EngineStatus(kind="tts", engine=self.name, available=False, model=self.model_name,
                               detail="Groq API key is not configured.")
        if importlib.util.find_spec("httpx") is None:
            return EngineStatus(kind="tts", engine=self.name, available=False, model=self.model_name,
                               detail='Groq TTS dependency missing. Install with: python -m pip install -e ".[voice-cloud]".')
        return EngineStatus(kind="tts", engine=self.name, available=True, model=self.model_name,
                           detail="Groq Orpheus English TTS is ready. Prompt text is sent to Groq for audio generation.")

    def synthesize(self, text: str) -> bytes:
        import httpx
        if not self.api_key:
            raise VoiceUnavailable("Groq API key is not configured. Local speech remains available.")
        if len(text) > self.max_characters:
            raise TextToSpeechError(
                "This prompt exceeds Groq Orpheus's 200-character input limit. Use the local voice or read it on screen."
            )
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model_name, "input": text, "voice": self.voice_name, "response_format": "wav"},
                )
                response.raise_for_status()
                audio = response.content
        except httpx.TimeoutException as exc:
            raise TextToSpeechError("Groq speech generation timed out. Read the question or try again.") from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 401:
                message = "Groq rejected the API key. Check GROQ_API_KEY and restart Prepped."
            elif code == 429:
                message = "Groq's voice quota or rate limit was reached. Local voice fallback will be used."
            elif code in (400, 413):
                message = "Groq could not generate audio for this prompt. Read it on screen or use local voice."
            else:
                message = f"Groq speech service returned HTTP {code}. Local voice fallback will be used."
            raise TextToSpeechError(message) from exc
        except httpx.HTTPError as exc:
            raise TextToSpeechError("Could not reach Groq speech service. Local voice fallback will be used.") from exc
        if not audio.startswith(b"RIFF") or b"WAVE" not in audio[:16]:
            raise TextToSpeechError("Groq returned an unsupported audio response. Local voice fallback will be used.")
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

    def synthesize(self, text: str, *, speed: float = 1.0) -> bytes:
        if not self.binary:
            raise VoiceUnavailable(
                "No local text-to-speech engine is installed. Read the question on screen."
            )
        clamped = max(0.7, min(1.5, float(speed or 1.0)))
        wpm_arg = str(max(100, min(240, round(150 * clamped))))
        try:
            result = subprocess.run(
                [self.binary, "-v", "en-us", "-s", wpm_arg, "-p", "45", "--stdout"],
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
