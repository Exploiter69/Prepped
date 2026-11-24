"""Regression checks for the four-screen UI design reference (v1).

These checks keep the authored visual direction attached to the real app
without introducing a screenshot fixture, remote font, or design dependency.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def test_reference_theme_and_persistent_navigation_are_local_first() -> None:
    reference = CSS.split("/* UI design reference v1", 1)[1]
    assert "--bg: #F6F2EA" in reference
    assert "--panel: #FFFCF7" in reference
    assert "--accent-strong: #0E2F2B" in reference
    assert 'Georgia, "Iowan Old Style", "Palatino Linotype", serif' in reference
    assert ".site-header" in reference and "position: fixed" in reference
    assert "@media (max-width: 720px)" in reference
    assert "@media (prefers-reduced-motion: reduce)" in CSS
    assert "fonts.googleapis.com" not in HTML + CSS
    assert "fonts.gstatic.com" not in HTML + CSS


def test_today_reference_hierarchy_keeps_the_primary_action_first() -> None:
    today = HTML.split('<section id="dashboard-view"', 1)[1].split("</section>", 1)[0]
    assert 'id="dashboard-hero-title"' in HTML
    assert 'id="dashboard-path-preview"' in HTML
    assert 'id="dashboard-plan-preview"' in HTML
    assert 'id="profile-panel"' in HTML
    assert ".dashboard-view > .dashboard-hero { order: 1; }" in CSS
    assert ".dashboard-view > .dashboard-columns { order: 3; }" in CSS
    assert ".dashboard-view > #profile-panel { order: 4; }" in CSS


def test_rehearsal_reference_preserves_voice_and_editable_text_fallback() -> None:
    practice = HTML.split('<section id="practice-view"', 1)[1].split("</section>", 1)[0]
    for control in ("id=\"practice-progress-track\"", "id=\"tts-play-button\"",
                    "id=\"record-button\"", "id=\"stop-recording-button\"",
                    "id=\"answer-input\""):
        assert control in HTML
    assert "editable" in HTML.lower()
    assert "aria-valuetext" in HTML
    assert ".practice-question-card" in CSS
    assert ".practice-answer-form" in CSS


def test_career_studios_and_memory_are_distinct_reference_workspaces() -> None:
    assert 'id="career-studio-list"' in HTML
    assert 'id="career-view"' in HTML
    assert ".career-studio-list { display: grid; grid-template-columns: repeat(3" in CSS
    assert 'id="memory-view"' in HTML
    assert 'id="memory-review"' in HTML
    assert ".memory-focus > :not(#memory-view)" in CSS
    assert "#learning-view.memory-focus > #memory-view" in CSS
    assert 'id="memory-toggle"' in HTML
    assert '$("#memory-toggle").addEventListener("click"' in APP
    assert 'setAttribute("aria-current", "page")' in APP
