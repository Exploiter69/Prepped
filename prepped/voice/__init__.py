"""Local voice adapters for Prepped.

The voice layer is deliberately small and replaceable. Speech-to-text and
text-to-speech engines expose narrow interfaces so another local engine can be
substituted without changing the session or feedback code.
"""
from prepped.voice.service import VoiceService, build_voice_service
from prepped.voice.stt import GroqWhisperSTT, SpeechToTextEngine, VoskSTT
from prepped.voice.tts import EspeakTTS, GroqOrpheusTTS, PiperTTS, TextToSpeechEngine

__all__ = [
    "VoiceService",
    "build_voice_service",
    "SpeechToTextEngine",
    "VoskSTT",
    "GroqWhisperSTT",
    "TextToSpeechEngine",
    "EspeakTTS",
    "GroqOrpheusTTS",
    "PiperTTS",
]
