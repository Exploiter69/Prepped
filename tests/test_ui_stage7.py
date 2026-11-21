from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "dashboard.js").read_text(encoding="utf-8")
LEARNING = (ROOT / "static" / "learning.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def test_stage7_dashboard_has_live_refresh_and_status_feedback() -> None:
    assert 'id="dashboard-refresh"' in HTML
    assert 'id="dashboard-load-status" role="status" aria-live="polite"' in HTML
    assert 'addEventListener("click",loadDashboard)' in JS
    assert "Some dashboard details could not be refreshed" in JS


def test_stage7_next_unfinished_dashboard_lesson_is_actionable() -> None:
    assert "dashboard-lesson-action" in JS
    assert "prepped:start-lesson" in JS
    assert 'window.addEventListener("prepped:start-lesson"' in LEARNING
    assert "completed the lessons currently listed in this path" in JS


def test_stage7_dashboard_action_and_refresh_are_mobile_and_motion_aware() -> None:
    assert "@media(max-width:620px)" in CSS
    assert ".dashboard-lesson-action" in CSS
    assert "@media(prefers-reduced-motion:reduce)" in CSS
