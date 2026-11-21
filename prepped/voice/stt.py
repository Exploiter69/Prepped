"""Local speech-to-text engines.

Vosk is the first adapter because its Python wheel works on CPU, the small
English model is about 40 MB compressed, and it needs no cloud account. The
model is never downloaded at application startup; see docs/VOICE.md.
"""
from __future__ import annotations

import importlib.util
import json
import threading
from pathlib import Path

from prepped.voice.base import EngineStatus, SpeechToTextEngine
from prepped.voice.errors import NoSpeechDetected, SpeechEngineError, VoiceUnavailable


class VoskSTT(SpeechToTextEngine):
    """Vosk/Kaldi offline recogniser using a model directory on disk."""

    name = "vosk"

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = Path(model_dir)
        self._model = None
        self._load_lock = threading.Lock()
        self._recognise_lock = threading.Lock()

    def _model_present(self) -> bool:
        required = ("am", "conf", "graph")
        return self.model_dir.is_dir() and all((self.model_dir / part).is_dir() for part in required)

    def status(self) -> EngineStatus:
        if not self._model_present():
            return EngineStatus(
                kind="stt",
                engine=self.name,
                available=False,
                model=self.model_dir.name,
                detail=(
                    "Local speech-to-text model not found. Run ./scripts/setup_voice.sh "
                    "once, then restart Prepped. Text input still works."
                ),
            )
        if importlib.util.find_spec("vosk") is None:
            return EngineStatus(
                kind="stt",
                engine=self.name,
                available=False,
                model=self.model_dir.name,
                detail=(
                    "The Vosk Python package is not installed. Run "
                    "python -m pip install -e '.[voice]' or use the setup script. "
                    "Text input still works."
                ),
            )
        return EngineStatus(
            kind="stt",
            engine=self.name,
            available=True,
            model=self.model_dir.name,
            detail="Local Vosk speech-to-text model is installed.",
        )

    def _load_model(self):
        with self._load_lock:
            if self._model is None:
                try:
                    from vosk import Model
                except ImportError as exc:  # pragma: no cover - status covers this
                    raise VoiceUnavailable(
                        "The Vosk Python package is not installed. Use text input or run the voice setup script."
                    ) from exc
                try:
                    self._model = Model(str(self.model_dir))
                except Exception as exc:  # Vosk raises generic exceptions for bad models
                    raise SpeechEngineError(
                        "The local speech model could not be loaded. Check the setup instructions or type your answer."
                    ) from exc
            return self._model

    def transcribe(self, pcm: bytes) -> str:
        if not pcm:
            raise NoSpeechDetected("No audio was received. Try recording again or type your answer.")

        model = self._load_model()
        try:
            from vosk import KaldiRecognizer
        except ImportError as exc:  # pragma: no cover
            raise VoiceUnavailable(
                "The Vosk Python package is not installed. Use text input or run the voice setup script."
            ) from exc

        try:
            # Serialise recognisers for predictable CPU and memory use on a
            # single-user local app. The shared model is read-only.
            with self._recognise_lock:
                recognizer = KaldiRecognizer(model, 16_000)
                for start in range(0, len(pcm), 4_000):
                    recognizer.AcceptWaveform(pcm[start : start + 4_000])
                result = json.loads(recognizer.FinalResult())
        except Exception as exc:
            raise SpeechEngineError(
                "Local speech-to-text failed while reading the recording. Try again or type your answer."
            ) from exc

        text = " ".join(str(result.get("text", "")).split())
        if not text:
            raise NoSpeechDetected(
                "No clear speech was recognised. Try again closer to the microphone or type your answer."
            )
        return text


class GroqWhisperSTT(SpeechToTextEngine):
    """Groq-hosted fast Whisper transcription adapter (opt-in via GROQ_API_KEY).

    PCM is wrapped as an in-memory WAV and sent directly to Groq. No audio
    file is written to disk. The API key is read only by the server process.
    """

    name = "groq-whisper"
    remote = True
    endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"
    model_name = "whisper-large-v3-turbo"

    def __init__(self, api_key: str, *, timeout_seconds: float = 45.0) -> None:
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds

    def status(self) -> EngineStatus:
        if not self.api_key:
            return EngineStatus(
                kind="stt", engine=self.name, available=False,
                model=self.model_name,
                detail="Groq API key is not configured. Set GROQ_API_KEY or use local Vosk.",
            )
        try:
            import httpx  # noqa: F401
        except ImportError:
            return EngineStatus(
                kind="stt", engine=self.name, available=False,
                model=self.model_name,
                detail='Groq transcription dependency missing. Install with: python -m pip install -e ".[voice-cloud]".',
            )
        return EngineStatus(
            kind="stt", engine=self.name, available=True,
            model=self.model_name,
            detail="Groq Whisper is ready. Recorded audio is sent to Groq for transcription.",
        )

    @staticmethod
    def _wav_bytes(pcm: bytes) -> bytes:
        import io
        import wave

        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16_000)
            wav.writeframes(pcm)
        return output.getvalue()

    def transcribe(self, pcm: bytes) -> str:
        import httpx

        if not self.api_key:
            raise VoiceUnavailable("Groq API key is not configured. Set GROQ_API_KEY or use local Vosk.")
        wav_bytes = self._wav_bytes(pcm)
        prompt = (
            "Transcribe this Indian English placement-interview answer accurately. "
            "Preserve the speaker's actual words, technical terms, names, and grammar. "
            "Do not summarize, translate, rewrite, or add words."
        )
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"model": self.model_name, "response_format": "json", "language": "en", "prompt": prompt},
                    files={"file": ("answer.wav", wav_bytes, "audio/wav")},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise SpeechEngineError("Groq transcription timed out. Try a shorter recording or type your answer.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 401:
                message = "Groq rejected the API key. Check GROQ_API_KEY and restart Prepped."
            elif status == 429:
                message = "Groq's free API limit was reached. Wait for the limit to reset or type your answer."
            elif status in (400, 413):
                message = "Groq could not process this recording. Try recording again or type your answer."
            else:
                message = f"Groq transcription service returned HTTP {status}. You can type your answer instead."
            raise SpeechEngineError(message) from exc
        except httpx.HTTPError as exc:
            raise SpeechEngineError("Could not reach Groq transcription. Check your internet connection or type your answer.") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise SpeechEngineError("Groq returned an unreadable transcription response. You can type your answer instead.") from exc

        if not isinstance(payload, dict):
            raise SpeechEngineError("Groq returned an unreadable transcription response. You can type your answer instead.")
        text = payload.get("text", "")
        if not isinstance(text, str) or not text.strip():
            raise NoSpeechDetected("Groq did not detect speech. Try recording again or type your answer.")
        return text.strip()
