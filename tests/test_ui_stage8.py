from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def test_stage8_skip_link_and_main_landmark_are_keyboard_reachable() -> None:
    assert 'class="skip-link" href="#main-content"' in HTML
    assert 'id="main-content" class="app-main" tabindex="-1"' in HTML
    assert ".skip-link:focus-visible" in CSS


def test_stage8_all_workspace_views_have_programmatic_focus_targets() -> None:
    view_ids = (
        "dashboard-view", "home-view", "practice-view", "feedback-view",
        "history-view", "learning-view", "career-view", "progress-view",
    )
    for view_id in view_ids:
        match = re.search(r'<section id="' + re.escape(view_id) + r'"[^>]*>', HTML)
        assert match, f"missing workspace view: {view_id}"
        assert 'tabindex="-1"' in match.group(0), f"view cannot receive navigation focus: {view_id}"


def test_stage8_primary_navigation_has_one_current_page_and_no_disclosure_semantics() -> None:
    nav = HTML.split('<nav class="header-actions"', 1)[1].split("</nav>", 1)[0]
    assert nav.count('aria-current="page"') == 1
    for button_id in (
        "home-toggle", "learning-toggle", "practice-toggle",
        "career-toggle", "progress-toggle", "history-toggle",
    ):
        assert f'id="{button_id}"' in nav
    assert "aria-expanded" not in nav
    assert 'aria-controls="history-view"' in nav


def test_stage8_navigation_state_and_motion_preference_are_synchronized() -> None:
    assert "navigationViews" in APP
    assert 'button.classList.toggle("is-active", current)' in APP
    assert 'button.setAttribute("aria-current", "page")' in APP
    assert 'button.removeAttribute("aria-current")' in APP
    assert 'reduceMotion ? "auto" : "smooth"' in APP


def test_stage8_controls_have_consistent_minimum_targets_and_visible_focus() -> None:
    assert "button:not(.nav-button) { min-height: 44px; }" in CSS
    assert 'select { min-height: 44px; }' in CSS
    assert ":focus-visible" in CSS
    assert "@media(prefers-reduced-motion:reduce)" in CSS
