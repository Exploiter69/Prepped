"""Public voice-layer errors with safe, learner-facing messages."""
from __future__ import annotations


class VoiceError(Exception):
    """Base error for expected local voice failures."""

    status_code = 500
    public_message = "Local voice processing failed. You can type your answer instead."

    def __init__(self, public_message: str | None = None) -> None:
        self.public_message = public_message or self.public_message
        super().__init__(self.public_message)


class VoiceUnavailable(VoiceError):
    """A required local engine, model, or system tool is not installed."""

    status_code = 503
    public_message = "Local voice is not available. You can type your answer instead."


class InvalidAudio(VoiceError):
    """The uploaded recording is empty, too large, or could not be decoded."""

    status_code = 400
    public_message = "The recording could not be read. Try again with a shorter recording or type your answer."


class AudioTooLarge(InvalidAudio):
    """The recording exceeds the configured in-memory limit."""

    status_code = 413
    public_message = "The recording is too long to transcribe. Keep it under the displayed limit or type your answer."


class NoSpeechDetected(VoiceError):
    """The audio decoded successfully but contained no recognisable speech."""

    status_code = 422
    public_message = "No speech was detected. Try recording again or type your answer."


class SpeechEngineError(VoiceError):
    """The speech engine failed after being selected."""

    status_code = 500
    public_message = "Local speech-to-text failed. You can type your answer instead."


class TextToSpeechError(VoiceError):
    """The local text-to-speech engine failed."""

    status_code = 500
    public_message = "Local spoken prompts are unavailable. Read the question on screen instead."


class InvalidSpeechText(VoiceError):
    """Text sent for synthesis is empty or exceeds the configured bound."""

    status_code = 422
    public_message = "The question text could not be spoken. Read the question on screen instead."
