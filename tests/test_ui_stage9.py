from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
RELEASE = (ROOT / "docs" / "PHASE_L_ACCEPTANCE.md").read_text(encoding="utf-8")
HELPER = (ROOT / "scripts" / "prepped.sh").read_text(encoding="utf-8")


def test_stage9_primary_workspaces_are_integrated_and_named() -> None:
    destinations = {
        "home-toggle": ("dashboard-view", "Today"),
        "practice-toggle": ("home-view", "Practice"),
        "learning-toggle": ("learning-view", "Learn"),
        "career-toggle": ("career-view", "Career"),
        "memory-toggle": ("memory-view", "Memory"),
        "progress-toggle": ("progress-view", "Progress"),
        "history-toggle": ("history-view", "History"),
    }
    nav = HTML.split('<nav class="header-actions"', 1)[1].split("</nav>", 1)[0]
    assert nav.count('aria-current="page"') == 1
    assert 'id="profile-nav-toggle"' in nav
    assert 'aria-controls="profile-view"' in nav
    assert ">Profile</span>" in nav
    for control, (view, label) in destinations.items():
        assert f'id="{control}"' in nav
        assert f'aria-controls="{view}"' in nav
        assert re.search(r'<section id="' + re.escape(view) + r'"[^>]*aria-labelledby=', HTML)
        assert f">{label}</span>" in nav
    assert "navigationViews" in APP


def test_stage9_release_entry_points_are_linked_and_truthful() -> None:
    assert "docs/UI_STAGE_9_ACCEPTANCE.md" in README
    assert "docs/PHASE_L_ACCEPTANCE.md" in README
    assert "source checkout" in RELEASE.lower()
    assert "manual" in RELEASE.lower()
    assert "release tag" in RELEASE.lower()
    assert "not" in RELEASE.lower()


def test_stage9_release_verification_remains_local_and_loopback_only() -> None:
    assert 'verify)' in HELPER
    assert '"$PYTHON" -m pytest -q' in HELPER
    assert '--host 127.0.0.1' in HELPER
    assert 'ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"' in HELPER
    assert "never resets learner data" in HELPER
    assert "reset" in HELPER.lower()
    assert "voice-setup)" in HELPER
