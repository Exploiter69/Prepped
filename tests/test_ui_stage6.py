from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "static" / "history-memory.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def test_stage6_history_has_search_filters_and_live_status() -> None:
    for marker in ('id="history-search"', 'id="history-filter"', 'id="history-timeline-list"', 'role="status"'):
        assert marker in HTML
    assert 'option value="lesson"' in HTML and 'option value="review"' in HTML
    assert 'addEventListener("input",render)' in JS
    assert 'addEventListener("change",render)' in JS


def test_stage6_timeline_uses_saved_activity_and_keeps_records_honest() -> None:
    assert "/api/progress/overview" in JS
    assert "recent_activity" in JS
    assert "records of practice, not a score" in JS
    assert "local" in HTML.lower()


def test_stage6_history_can_open_existing_learning_destinations() -> None:
    for kind in ("practice", "interview", "review", "lesson"):
        assert f'{kind}:' in JS
    assert 'open.dataset.sessionId = session.id' in APP
    assert 'Open Memory' in JS and 'Open Career' in JS


def test_stage6_timeline_responsive_and_keyboard_native_controls() -> None:
    assert ".history-timeline-entry" in CSS
    assert "@media(max-width:620px)" in CSS
    assert '<input id="history-search" type="search"' in HTML
    assert '<select id="history-filter">' in HTML
