from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prepped.main import create_app
from prepped.voice.base import EngineStatus
from prepped.voice.errors import InvalidAudio, TextToSpeechError
from prepped.voice.service import VoiceService, VoiceSettings
from prepped.voice.stt import VoskSTT
from prepped.voice.tts import EspeakTTS, PiperTTS


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "scenarios" / "project-explanation.v1.json"


class FakeDecoder:
    def __init__(self, pcm: bytes = b"\x00\x00" * 16_000, error: Exception | None = None) -> None:
        self.pcm = pcm
        self.error = error
        self.calls: list[tuple[bytes, int]] = []

    def __call__(self, audio: bytes, *, max_seconds: int = 60) -> bytes:
        self.calls.append((audio, max_seconds))
        if self.error:
            raise self.error
        return self.pcm


class FakeSTT:
    name = "fake-vosk"

    def __init__(self, text: str = "I built a small local project.", available: bool = True, detail: str = "Fake STT ready.") -> None:
        self.text = text
        self.available = available
        self.detail = detail
        self.calls: list[bytes] = []

    def status(self) -> EngineStatus:
        return EngineStatus(
            kind="stt",
            engine=self.name,
            available=self.available,
            detail=self.detail,
            model="fake-model",
        )

    def transcribe(self, pcm: bytes) -> str:
        self.calls.append(pcm)
        return self.text


class FakeTTS:
    name = "fake-tts"

    def __init__(self, available: bool = True, detail: str = "Fake TTS ready.", error: Exception | None = None) -> None:
        self.available = available
        self.detail = detail
        self.error = error
        self.calls: list[str] = []

    def status(self) -> EngineStatus:
        return EngineStatus(
            kind="tts",
            engine=self.name,
            available=self.available,
            detail=self.detail,
            model="fake-voice",
        )

    def synthesize(self, text: str) -> bytes:
        self.calls.append(text)
        if self.error:
            raise self.error
        return b"RIFF\x00\x00\x00\x00WAVEfmt "


def make_client(
    tmp_path: Path,
    *,
    stt: FakeSTT | None = None,
    tts: FakeTTS | None = None,
    decoder: FakeDecoder | None = None,
    settings: VoiceSettings | None = None,
) -> tuple[TestClient, VoiceService]:
    service = VoiceService(
        stt or FakeSTT(),
        tts or FakeTTS(),
        decoder=decoder or FakeDecoder(),
        settings=settings,
    )
    client = TestClient(
        create_app(
            db_path=tmp_path / "voice.sqlite3",
            scenario_path=SCENARIO_PATH,
            voice_service=service,
        )
    )
    client.__enter__()
    return client, service


def test_voice_status_exposes_local_engines_privacy_and_limits(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        response = client.get("/api/voice/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["stt"]["available"] is True
        assert payload["tts"]["available"] is True
        assert payload["limits"]["max_recording_seconds"] == 60
        assert "does not save raw audio" in payload["privacy"]
        assert "text input" in payload["fallback"].lower()
    finally:
        client.__exit__(None, None, None)


def test_transcription_returns_editable_text_and_never_stores_audio(tmp_path: Path) -> None:
    stt = FakeSTT(text="I implemented the FastAPI endpoints.")
    decoder = FakeDecoder()
    client, _ = make_client(tmp_path, stt=stt, decoder=decoder)
    try:
        response = client.post(
            "/api/voice/transcribe",
            content=b"fake-webm-audio",
            headers={"Content-Type": "audio/webm;codecs=opus"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["text"] == "I implemented the FastAPI endpoints."
        assert payload["engine"] == "fake-vosk"
        assert payload["stored_audio"] is False
        assert decoder.calls == [(b"fake-webm-audio", 60)]
        assert stt.calls == [b"\x00\x00" * 16_000]
        assert list(tmp_path.rglob("*.webm")) == []
    finally:
        client.__exit__(None, None, None)


def test_missing_stt_model_returns_clear_fallback_without_decoding(tmp_path: Path) -> None:
    stt = FakeSTT(
        available=False,
        detail="Local speech-to-text model not found. Run ./scripts/setup_voice.sh once. Text input still works.",
    )
    decoder = FakeDecoder()
    client, _ = make_client(tmp_path, stt=stt, decoder=decoder)
    try:
        response = client.post("/api/voice/transcribe", content=b"audio", headers={"Content-Type": "audio/webm"})
        assert response.status_code == 503
        assert "setup_voice.sh" in response.json()["detail"]
        assert decoder.calls == []
    finally:
        client.__exit__(None, None, None)


def test_empty_oversized_and_undecodable_audio_are_rejected(tmp_path: Path) -> None:
    client, _ = make_client(
        tmp_path,
        decoder=FakeDecoder(error=InvalidAudio("The browser recording could not be decoded.")),
        settings=VoiceSettings(max_audio_bytes=10),
    )
    try:
        empty = client.post("/api/voice/transcribe", content=b"")
        assert empty.status_code == 400

        oversized = client.post("/api/voice/transcribe", content=b"x" * 11)
        assert oversized.status_code == 413
        assert "too long" in oversized.json()["detail"]

        undecodable = client.post("/api/voice/transcribe", content=b"xxxx")
        assert undecodable.status_code == 400
        assert "could not be decoded" in undecodable.json()["detail"]
    finally:
        client.__exit__(None, None, None)


def test_transcription_stream_limit_applies_without_content_length(tmp_path: Path) -> None:
    client, _ = make_client(
        tmp_path,
        settings=VoiceSettings(max_audio_bytes=10),
    )
    try:
        # An iterable request body is sent without a precomputed Content-Length.
        response = client.post(
            "/api/voice/transcribe",
            content=iter([b"12345678", b"9012"]),
            headers={"Content-Type": "audio/webm"},
        )
        assert response.status_code == 413
        assert "too long" in response.json()["detail"]
    finally:
        client.__exit__(None, None, None)


def test_tts_returns_local_wav_and_validates_text(tmp_path: Path) -> None:
    tts = FakeTTS()
    client, _ = make_client(tmp_path, tts=tts)
    try:
        response = client.post("/api/voice/tts", json={"text": "  Tell me about your project.  "})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/wav")
        assert response.headers["cache-control"] == "no-store"
        assert response.content.startswith(b"RIFF")
        assert tts.calls == ["Tell me about your project."]

        empty = client.post("/api/voice/tts", json={"text": ""})
        assert empty.status_code == 422
        too_long = client.post("/api/voice/tts", json={"text": "x" * 1_201})
        assert too_long.status_code == 422
    finally:
        client.__exit__(None, None, None)


def test_unavailable_tts_and_engine_failure_keep_text_mode_usable(tmp_path: Path) -> None:
    unavailable = FakeTTS(available=False, detail="No local voice installed. Read the question instead.")
    client, _ = make_client(tmp_path, tts=unavailable)
    try:
        response = client.post("/api/voice/tts", json={"text": "Question"})
        assert response.status_code == 503
        assert "Read the question" in response.json()["detail"]

        session = client.post("/api/sessions")
        assert session.status_code == 201
        answer = client.post(
            f"/api/sessions/{session.json()['id']}/answers",
            json={"question_id": "project_overview", "answer_text": "Typed answer still works."},
        )
        assert answer.status_code == 200
    finally:
        client.__exit__(None, None, None)

    failing = FakeTTS(error=TextToSpeechError())
    client, _ = make_client(tmp_path, tts=failing)
    try:
        response = client.post("/api/voice/tts", json={"text": "Question"})
        assert response.status_code == 500
        assert "Read the question" in response.json()["detail"]
    finally:
        client.__exit__(None, None, None)


def test_text_session_works_when_both_voice_engines_are_unavailable(tmp_path: Path) -> None:
    client, _ = make_client(
        tmp_path,
        stt=FakeSTT(available=False, detail="STT missing."),
        tts=FakeTTS(available=False, detail="TTS missing."),
    )
    try:
        status = client.get("/api/voice/status").json()
        assert status["stt"]["available"] is False
        assert status["tts"]["available"] is False

        started = client.post("/api/sessions")
        assert started.status_code == 201
        answer = client.post(
            f"/api/sessions/{started.json()['id']}/answers",
            json={"question_id": "project_overview", "answer_text": "Text mode remains fully usable."},
        )
        assert answer.status_code == 200
        assert answer.json()["answered_count"] == 1
    finally:
        client.__exit__(None, None, None)


def test_frontend_serves_voice_controls_and_script(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    try:
        home = client.get("/")
        script = client.get("/static/voice.js")
        assert home.status_code == 200
        assert "Start recording" in home.text
        assert "Play question aloud" in home.text
        assert script.status_code == 200
        assert "MediaRecorder" in script.text
        assert "/api/voice/transcribe" in script.text
        assert "stopAll" in script.text
        assert "permissionPending" in script.text
        assert "requestGeneration !== state.generation" in script.text
        assert "const requestGeneration = state.generation" in script.text
        assert "state.transcriptionController?.abort()" in script.text
        assert "state.ttsController?.abort()" in script.text
        assert "signal: controller.signal" in script.text
    finally:
        client.__exit__(None, None, None)


def test_vosk_status_explains_how_to_install_missing_model(tmp_path: Path) -> None:
    status = VoskSTT(tmp_path / "missing-model").status()
    assert status.available is False
    assert "setup_voice.sh" in status.detail


def test_piper_status_explains_missing_voice_model(tmp_path: Path) -> None:
    status = PiperTTS(tmp_path / "missing.onnx").status()
    assert status.available is False
    assert "Piper" in status.detail


@pytest.mark.skipif(not EspeakTTS().status().available, reason="espeak-ng is not installed")
def test_espeak_adapter_returns_a_local_wav() -> None:
    audio = EspeakTTS().synthesize("Tell me about your project.")
    assert audio.startswith(b"RIFF")
    assert b"WAVE" in audio[:16]


def test_groq_adapter_wraps_pcm_as_wav_and_returns_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from prepped.voice.stt import GroqWhisperSTT

    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"text": "I built a placement preparation application."}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            captured["timeout"] = kwargs["timeout"]

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, **kwargs: object) -> FakeResponse:
            captured["url"] = url
            captured.update(kwargs)
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    pcm = b"\x00\x00" * 16_000
    transcript = GroqWhisperSTT("test-key").transcribe(pcm)

    assert transcript == "I built a placement preparation application."
    assert captured["url"] == GroqWhisperSTT.endpoint
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    assert captured["data"]["model"] == "whisper-large-v3"  # type: ignore[index]
    upload = captured["files"]["file"]  # type: ignore[index]
    assert upload[0] == "answer.wav"
    assert upload[2] == "audio/wav"
    assert upload[1].startswith(b"RIFF")


def test_groq_adapter_maps_rate_limit_without_leaking_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from prepped.voice.errors import SpeechEngineError
    from prepped.voice.stt import GroqWhisperSTT

    class FakeResponse:
        status_code = 429

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> object:
            request = httpx.Request("POST", GroqWhisperSTT.endpoint)
            response = httpx.Response(429, request=request)
            raise httpx.HTTPStatusError("private provider detail", request=request, response=response)

    monkeypatch.setattr(httpx, "Client", FakeClient)
    with pytest.raises(SpeechEngineError, match="free API limit"):
        GroqWhisperSTT("test-key").transcribe(b"\x00\x00" * 16_000)


def test_remote_stt_status_discloses_remote_audio_processing() -> None:
    from prepped.voice.stt import GroqWhisperSTT

    service = VoiceService(GroqWhisperSTT("test-key"), FakeTTS())
    assert "sent to Groq" in service.status()["privacy"]
