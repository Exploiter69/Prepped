"""Tests for Packs A, B, C, and D:
- Pack A: speaking analytics, transcript evidence mapping, attempt comparisons
- Pack B: 12-week activity heatmap, preferences, TTS speed, PWA manifest/SW
- Pack C: project studio, local resume parser, timed mocks, warm-ups, debriefs
- Pack D: provider-neutral cloud AI config, key privacy, consent enforcement, quota & outage fallback
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from prepped.ai_provider import AIProviderError, call_cloud_provider
from prepped.main import create_app
from prepped.speaking_analytics import analyze_transcript
from prepped.voice.base import EngineStatus, SpeechToTextEngine, TextToSpeechEngine
from prepped.voice.service import VoiceService


class _SpeedAwareStubTTS(TextToSpeechEngine):
    name = "stub-speed-tts"

    def __init__(self) -> None:
        self.speeds: list[float] = []

    def status(self) -> EngineStatus:
        return EngineStatus(kind="tts", engine=self.name, available=True, detail="Stub speed TTS ready.")

    def synthesize(self, text: str, *, speed: float = 1.0) -> bytes:
        self.speeds.append(speed)
        return b"RIFF\x24\x00\x00\x00WAVEfmt " + f"{speed:.2f}".encode("ascii")


class _StubSTT(SpeechToTextEngine):
    name = "stub-stt"

    def status(self) -> EngineStatus:
        return EngineStatus(kind="stt", engine=self.name, available=False, detail="Offline.")

    def transcribe(self, pcm_wav: bytes) -> str:
        return ""


def test_pack_a_speaking_analytics_evidence_and_comparison(tmp_path: Path) -> None:
    sample = (
        "Myself Alok, um I am having 2 years experience and I built the API endpoint with SQLite validation "
        "and automated tests because we needed reliability, and I didn't built a cloud server."
    )
    a1 = analyze_transcript(sample, duration_seconds=20.0, pause_count=2, silence_seconds=2.3)
    assert a1["word_count"] > 20
    assert a1["wpm"] is not None and a1["wpm"] > 50
    assert a1["filler_total"] >= 1
    assert a1["pause_analysis"]["pause_count"] == 2
    assert len(a1["grammar_observations"]) >= 3
    assert len(a1["relevant_vocabulary"]) >= 3
    assert any(h["category"] == "filler" for h in a1["highlights"])
    assert any(h["category"] == "grammar_hint" for h in a1["highlights"])
    assert any(h["category"] == "vocabulary" for h in a1["highlights"])

    # Typed answers without recording duration must not invent WPM.
    typed = analyze_transcript("I built a clean REST endpoint and verified validation tests.")
    assert typed["duration_seconds"] is None
    assert typed["wpm"] is None
    assert typed["pause_analysis"]["available"] is False

    app = create_app(db_path=tmp_path / "pack_a.sqlite3")
    with TestClient(app) as client:
        s1 = client.post("/api/sessions").json()
        for q in ["project_overview", "personal_contribution", "design_decision", "evidence_and_result", "reflection"]:
            r = client.post(
                f"/api/sessions/{s1['id']}/answers",
                json={
                    "question_id": q,
                    "answer_text": "Um basically we did the project and um I built the API endpoint.",
                    "speaking_duration_seconds": 12.0,
                    "pause_count": 1,
                    "silence_seconds": 1.2,
                },
            )
            assert r.status_code == 200
        fb1 = client.get(f"/api/sessions/{s1['id']}/feedback").json()
        assert fb1["delivery_summary"]["total_fillers"] > 0
        assert fb1["delivery_summary"]["average_wpm"] is not None
        assert fb1["delivery_summary"]["audio_retained"] is False

        s2 = client.post(f"/api/sessions/{s1['id']}/retry").json()
        for q in ["project_overview", "personal_contribution", "design_decision", "evidence_and_result", "reflection"]:
            client.post(
                f"/api/sessions/{s2['id']}/answers",
                json={
                    "question_id": q,
                    "answer_text": "Students needed a clear tracker. I built the SQLite API and tested validation endpoints because local speed mattered.",
                    "speaking_duration_seconds": 10.0,
                    "pause_count": 0,
                    "silence_seconds": 0.0,
                },
            )
        cmp_res = client.get(f"/api/sessions/{s2['id']}/comparison")
        assert cmp_res.status_code == 200
        cmp_body = cmp_res.json()
        assert cmp_body["has_previous"] is True
        assert cmp_body["comparison"]["metrics"]["filler_delta"] < 0


def test_pack_b_preferences_tts_speed_heatmap_and_pwa(tmp_path: Path) -> None:
    stub_tts = _SpeedAwareStubTTS()
    voice_service = VoiceService(_StubSTT(), stub_tts)
    app = create_app(db_path=tmp_path / "pack_b.sqlite3", voice_service=voice_service)
    with TestClient(app) as client:
        default_prefs = client.get("/api/preferences").json()["preferences"]
        assert default_prefs["tts_speed"] == 1.0
        assert default_prefs["theme"] == "light"

        saved = client.put(
            "/api/preferences",
            json={"tts_speed": 1.25, "theme": "dark", "text_size": "large", "ephemeral_audio_replay": False},
        )
        assert saved.status_code == 200
        assert saved.json()["preferences"]["tts_speed"] == 1.25
        assert saved.json()["preferences"]["theme"] == "dark"
        assert saved.json()["preferences"]["ephemeral_audio_replay"] is False

        bad_speed = client.put("/api/preferences", json={"tts_speed": 3.0})
        assert bad_speed.status_code == 422

        tts_resp = client.post("/api/voice/tts", json={"text": "Tell me about your project.", "speed": 1.25})
        assert tts_resp.status_code == 200
        assert stub_tts.speeds == [1.25]

        overview = client.get("/api/progress/overview").json()
        assert len(overview["activity_heatmap"]) == 84
        assert sum(d["count"] for d in overview["activity_heatmap"]) == 0

        manifest = client.get("/manifest.webmanifest")
        assert manifest.status_code == 200
        assert manifest.json()["short_name"] == "Prepped"
        sw = client.get("/sw.js")
        assert sw.status_code == 200
        assert 'url.pathname.startsWith("/api/")' in sw.text


def test_pack_c_project_studio_resume_prep_timed_mock_and_warmup(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "pack_c.sqlite3")
    with TestClient(app) as client:
        created = client.post(
            "/api/career/projects",
            json={
                "title": "Campus Timetable Helper",
                "personal_role": "Backend developer",
                "tech_stack": "Python, FastAPI, SQLite",
                "problem": "Students struggled to track room changes.",
                "approach": "Built a local-first web schedule with offline sync.",
                "implementation": "Implemented SQLite schema and REST endpoints.",
                "decisions_tradeoffs": "Chose SQLite over PostgreSQL for zero setup.",
                "outcome": "Verified with 30 automated pytest checks.",
                "learning": "Learned to isolate database migrations cleanly.",
            },
        )
        assert created.status_code == 201
        project = created.json()["project"]
        assert len(project["generated_questions"]) == 5

        resume = client.post(
            "/api/career/resume/parse",
            json={
                "resume_text": (
                    "Skills: Python, C++, FastAPI, SQLite, Linux, Git.\n"
                    "- Built an automated attendance checker used by 120 students with 40% faster lookup.\n"
                    "- Designed modular REST API validation and integration tests."
                ),
                "save_as_project": True,
            },
        )
        assert resume.status_code == 200
        rbody = resume.json()
        assert "Python" in rbody["detected_skills"]
        assert len(rbody["questions"]) >= 3
        assert rbody["saved_project"] is not None

        started = client.post(
            "/api/career/mocks",
            json={"mode": "project_studio", "project_id": project["id"], "time_limit_seconds": 600},
        )
        assert started.status_code == 201
        mock = started.json()["mock"]
        q1 = mock["current_question"]
        resp1 = client.post(
            f"/api/career/mocks/{mock['id']}/respond",
            json={
                "question_id": q1["id"],
                "answer_text": "I built the FastAPI backend and automated validation tests to solve timetable confusion.",
                "elapsed_seconds": 45,
                "speaking_duration_seconds": 12.0,
            },
        )
        assert resp1.status_code == 200
        finished = client.post(f"/api/career/mocks/{mock['id']}/finish", json={"elapsed_seconds": 90})
        assert finished.status_code == 200
        debrief = finished.json()["debrief"]
        assert debrief["responses_completed"] == 1
        assert debrief["elapsed_seconds"] == 90
        assert "does not score ability" in debrief["disclaimer"]

        warmup = client.post("/api/career/mocks", json={"mode": "warmup", "time_limit_seconds": 300})
        assert warmup.status_code == 201
        assert warmup.json()["mock"]["question_count"] == 4


def test_pack_d_cloud_ai_privacy_consent_key_handling_and_quota_fallback(tmp_path: Path) -> None:
    db_file = tmp_path / "pack_d.sqlite3"
    app = create_app(db_path=db_file)
    with TestClient(app) as client:
        cfg = client.get("/api/ai/config").json()["ai"]
        assert cfg["enabled"] is False
        assert cfg["provider"] == "none"

        secret = "secret-test-key-99999"
        key_res = client.post("/api/ai/key", json={"provider": "gemini", "api_key": secret})
        assert key_res.status_code == 200
        assert secret not in key_res.text

        client.put(
            "/api/ai/config",
            json={"enabled": True, "provider": "gemini", "model": "gemini-2.5-flash", "consent_acknowledged": True, "daily_request_limit": 2},
        )
        cfg_after = client.get("/api/ai/config")
        assert cfg_after.status_code == 200
        assert secret not in cfg_after.text
        assert cfg_after.json()["ai"]["has_api_key"] is True

        export_res = client.get("/api/data/export")
        assert export_res.status_code == 200
        assert secret not in export_res.text

        no_consent = client.post(
            "/api/ai/assist",
            json={"task": "transcript_feedback", "content": "I built a small API.", "consent_confirmed": False},
        )
        assert no_consent.status_code == 400
        assert "consent" in no_consent.json()["detail"].lower()

    def _mock_429(url, headers, payload, timeout):
        return 429, {"error": {"message": "Quota exceeded"}}

    def _mock_401(url, headers, payload, timeout):
        return 401, {"error": {"message": "Invalid key"}}

    def _mock_404(url, headers, payload, timeout):
        return 404, {"error": {"message": "Model not found"}}

    def _mock_ok(url, headers, payload, timeout):
        return 200, {"candidates": [{"content": {"parts": [{"text": "Strengths: Clear role."}]}}]}

    try:
        call_cloud_provider("gemini", "gemini-2.5-flash", "k", "sys", "usr", http_post=_mock_429)
        assert False, "Expected 429 error"
    except AIProviderError as exc:
        assert exc.status_code == 429 and "offline" in exc.public_message.lower()

    try:
        call_cloud_provider("groq", "llama-3.3-70b-versatile", "k", "sys", "usr", http_post=_mock_401)
        assert False, "Expected 401 error"
    except AIProviderError as exc:
        assert exc.status_code == 401

    try:
        call_cloud_provider("gemini", "old-model", "k", "sys", "usr", http_post=_mock_404)
        assert False, "Expected 404 error"
    except AIProviderError as exc:
        assert exc.status_code == 400 and "model" in exc.public_message.lower()

    reply = call_cloud_provider("gemini", "gemini-2.5-flash", "k", "sys", "usr", http_post=_mock_ok)
    assert "Clear role" in reply


def test_scientific_curriculum_and_fluency_432_drill(tmp_path: Path) -> None:
    app = create_app(db_path=tmp_path / "sci.sqlite3")
    with TestClient(app) as client:
        catalog = client.get("/api/learning/catalog").json()
        assert len(catalog["levels"]) == 3
        assert len(catalog["units"]) == 14
        lessons_by_id = {lesson["id"]: lesson for track in catalog["tracks"] for lesson in track["lessons"]}
        assert len(lessons_by_id) == 46
        fluency_lesson = lessons_by_id["speaking-432-fluency"]
        assert fluency_lesson["method_tag"] == "4/3/2 Fluency Proceduralization"

        started = client.post("/api/career/mocks", json={"mode": "fluency_432", "time_limit_seconds": 240})
        assert started.status_code == 201
        mock = started.json()["mock"]
        assert mock["question_count"] == 3
        assert mock["questions"][0]["id"] == "fluency_432_r1"
        assert mock["questions"][0]["prompt"] == mock["questions"][2]["prompt"]

        r1 = client.post(
            f"/api/career/mocks/{mock['id']}/respond",
            json={
                "question_id": "fluency_432_r1",
                "answer_text": "Um basically I built a local SQLite app and um I tested the API endpoints.",
                "elapsed_seconds": 60,
                "speaking_duration_seconds": 30.0,
            },
        )
        assert r1.status_code == 200
        r2 = client.post(
            f"/api/career/mocks/{mock['id']}/respond",
            json={
                "question_id": "fluency_432_r2",
                "answer_text": "I built a local SQLite practice app and verified the API endpoints with automated tests.",
                "elapsed_seconds": 100,
                "speaking_duration_seconds": 20.0,
            },
        )
        assert r2.status_code == 200
        r3 = client.post(
            f"/api/career/mocks/{mock['id']}/respond",
            json={
                "question_id": "fluency_432_r3",
                "answer_text": "I built a local SQLite practice app and verified all API endpoints with automated regression tests.",
                "elapsed_seconds": 130,
                "speaking_duration_seconds": 15.0,
            },
        )
        assert r3.status_code == 200
        debrief = r3.json()["debrief"]
        assert any("4/3/2 Fluency Drill" in s for s in debrief["strengths"])
        assert any("4/3/2 Pace progression" in s for s in debrief["strengths"])
