"""Small interfaces shared by local speech engines."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EngineStatus:
    """Machine-readable availability for one local engine."""

    kind: str
    engine: str
    available: bool
    detail: str
    model: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpeechToTextEngine(Protocol):
    """A local speech-to-text engine operating on mono 16 kHz PCM."""

    name: str

    def status(self) -> EngineStatus: ...

    def transcribe(self, pcm: bytes) -> str: ...


class TextToSpeechEngine(Protocol):
    """A local text-to-speech engine returning a complete WAV byte string."""

    name: str

    def status(self) -> EngineStatus: ...

    def synthesize(self, text: str) -> bytes: ...
