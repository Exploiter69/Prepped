"""Opt-in integration check for the real local Vosk model.

This test skips on a clean checkout because models are intentionally not
committed. Run ./scripts/setup_voice.sh first to execute it locally.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from prepped.voice.audio import decode_audio_to_pcm
from prepped.voice.stt import VoskSTT


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "vosk-model-small-en-us-0.15"


@pytest.mark.skipif(not (MODEL_DIR / "am").is_dir(), reason="local Vosk model is not installed")
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
@pytest.mark.skipif(shutil.which("espeak-ng") is None, reason="espeak-ng is not installed")
def test_vosk_transcribes_synthesised_speech_end_to_end() -> None:
    wav = subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "150", "--stdout"],
        input=b"Tell me about a project you have worked on.",
        capture_output=True,
        check=True,
    ).stdout
    pcm = decode_audio_to_pcm(wav, max_seconds=30)

    engine = VoskSTT(MODEL_DIR)
    assert engine.status().available is True
    text = engine.transcribe(pcm)
    assert len(text.split()) >= 2
