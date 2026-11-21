from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
PROGRESS_JS = (ROOT / "static" / "progress.js").read_text(encoding="utf-8")
INTELLIGENCE_JS = (ROOT / "static" / "intelligence.js").read_text(encoding="utf-8")


def test_stage5_progress_story_and_live_summary_are_present() -> None:
    assert "YOUR LEARNING STORY / STAGE 5" in HTML
    assert 'id="progress-insight-note"' in HTML
    assert "progress-summary-stage5" in HTML
    assert "progress-insight-note" in CSS
    assert "Your starting point is simple" in PROGRESS_JS
    assert "These records show what you did—not how capable you are." in PROGRESS_JS


def test_weekly_activity_is_described_without_streak_or_gain_claims() -> None:
    assert 'id="progress-week-summary"' in HTML
    assert "last seven days" in PROGRESS_JS
    assert "not a streak or learning-gain measure" in PROGRESS_JS


def test_skill_cards_keep_lesson_evidence_not_skill_ratings() -> None:
    assert "Lesson evidence recorded" in PROGRESS_JS
    assert "Evidence not yet recorded" in PROGRESS_JS
    assert "Completed lesson evidence:" in PROGRESS_JS
    assert "lesson coverage, not a skill rating" in HTML


def test_stage5_layout_is_responsive_and_respects_reduced_motion() -> None:
    assert ".progress-stage5-intro" in CSS
    assert "@media (max-width:680px)" in CSS
    assert "@media (prefers-reduced-motion:reduce)" in CSS


def test_existing_progress_actions_and_plan_workflows_are_preserved() -> None:
    for element_id in (
        "progress-refresh", "progress-recommendations", "progress-goals",
        "progress-archived-goals", "data-export", "data-import",
        "intelligence-plan-items", "intelligence-week",
    ):
        assert f'id="{element_id}"' in HTML
    for endpoint in ("/api/progress/overview", "/api/goals", "/api/data/export", "/api/data/restore"):
        assert endpoint in PROGRESS_JS
    assert "/api/intelligence/plan" in INTELLIGENCE_JS
