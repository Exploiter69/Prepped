"""Real-browser acceptance tests for the local learner profile and practice flow.

These tests are enabled in CI with the optional browser-test extra. A normal
application install does not depend on Playwright or a browser binary.
"""
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

from prepped.main import create_app
from uvicorn import Config, Server


@pytest.fixture
def local_app_url(tmp_path: Path):
    """Run an isolated app/database on an ephemeral localhost port."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    server = Server(
        Config(
            create_app(db_path=tmp_path / "browser-acceptance.sqlite3"),
            host="127.0.0.1",
            port=port,
            log_level="error",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("Local Prepped test server did not start.")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def browser_page():
    with playwright_sync.sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


def test_profile_setup_edit_cancel_save_and_reload(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.wait_for_function(
        "() => document.querySelector('#profile-save-status').textContent === 'Not set up'"
    )
    page.locator("#profile-edit-toggle").click()

    form = page.locator("#profile-form")
    toggle = page.locator("#profile-edit-toggle")
    assert form.is_visible()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert page.locator("#profile-name").evaluate("(element) => document.activeElement === element")

    page.locator("#profile-name").fill("Test Learner")
    page.locator("#profile-year").select_option("2")
    page.locator("#profile-branch").fill("CSE")
    page.locator("#profile-goal").select_option("english_fluency")
    page.locator("#profile-confidence").select_option("beginner")
    page.locator('input[name="improvement_areas"][value="grammar"]').check()
    page.locator('input[name="improvement_areas"][value="vocabulary"]').check()
    page.locator("#profile-form button[type='submit']").click()

    page.wait_for_function(
        "() => document.querySelector('#profile-summary').textContent.includes('English fluency')"
    )
    assert not form.is_visible()
    assert toggle.get_attribute("aria-expanded") == "false"
    assert "Year 2" in page.locator("#profile-summary").inner_text()
    assert "CSE" in page.locator("#profile-summary").inner_text()
    assert "grammar and sentence construction" in page.locator("#profile-summary").inner_text()

    page.reload()
    page.wait_for_function(
        "() => document.querySelector('#profile-save-status').textContent === 'Saved locally'"
    )
    assert "English fluency" in page.locator("#profile-summary").inner_text()
    assert "Year 2" in page.locator("#profile-summary").inner_text()

    toggle.click()
    assert form.is_visible()
    page.locator("#profile-goal").select_option("placement_interviews")
    page.locator("#profile-cancel").click()
    page.wait_for_function(
        "() => document.querySelector('#profile-form').classList.contains('hidden')"
    )
    assert "English fluency" in page.locator("#profile-summary").inner_text()

    toggle.click()
    page.locator("#profile-goal").select_option("professional_communication")
    page.locator("#profile-form button[type='submit']").click()
    page.wait_for_function(
        "() => document.querySelector('#profile-summary').textContent.includes('Professional communication')"
    )
    page.reload()
    page.wait_for_function(
        "() => document.querySelector('#profile-summary').textContent.includes('Professional communication')"
    )


def test_practice_room_is_not_gated_by_profile_and_text_flow_completes(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.wait_for_function(
        "() => document.querySelector('#profile-save-status').textContent === 'Not set up'"
    )
    assert page.locator("#profile-form").is_hidden()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    page.locator("#answer-input").fill(
        "I built a small API and tested it with automated checks. "
        "I chose SQLite because the application runs locally."
    )
    page.locator("#submit-button").click()
    page.wait_for_function(
        "() => document.querySelector('#practice-progress').textContent === 'Question 2 of 5'"
    )

    for expected_question in range(3, 6):
        page.locator("#skip-button").click()
        page.wait_for_function(
            "(expected) => document.querySelector('#practice-progress').textContent === expected",
            arg=f"Question {expected_question} of 5",
        )
    page.locator("#skip-button").click()

    page.locator("#feedback-view").wait_for(state="visible", timeout=10000)
    assert "1 of 5 questions had non-empty answers" in page.locator("#feedback-summary").inner_text()
    assert "There is no overall score." in page.locator("#feedback-summary").inner_text()

    page.locator("#history-toggle").click()
    page.locator("#history-view").wait_for(state="visible")
    assert "project explanation" in page.locator("#history-list").inner_text()


def test_learning_workspace_completes_and_resumes_a_saved_lesson(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    assert "Placement communication" in page.locator("#learning-route-title").inner_text()
    assert page.locator(".learning-skill").count() >= 14
    assert "planned" in page.locator("#learning-skill-list").inner_text().lower()

    page.locator('button[data-lesson-id="sentence-building"]').click()
    page.locator("#learning-runner").wait_for(state="visible")
    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 2 of 3'"
    )

    # The attempt is durable: reload, find it in the resume area, and continue.
    page.reload()
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-resume-list').textContent.includes('Resume:')"
    )
    page.locator("#learning-resume-list button").click()
    page.locator("#learning-runner").wait_for(state="visible")
    assert "Exercise 2 of 3" in page.locator("#learning-exercise-count").inner_text()

    for position, token in enumerate(["a", "b", "c", "d"]):
        page.locator(".learning-order-select").nth(position).select_option(token)
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 3 of 3'"
    )
    page.locator("#learning-reflection").fill("I built a timetable app for my class.")
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-runner').textContent.includes('Lesson review')"
    )
    assert "saved for self review" in page.locator("#learning-feedback").inner_text().lower()
    assert "not automatically graded" in page.locator("#learning-feedback").inner_text().lower()
    assert "Lessons completed" in page.locator("#learning-progress").inner_text()
    next_lesson = page.locator("#learning-feedback button").filter(has_text="Next lesson: Grammar in context")
    assert next_lesson.is_visible()
    next_lesson.click()
    assert "Grammar in context" in page.locator("#learning-runner-title").inner_text()


def test_listening_lesson_has_playback_and_revealed_text_alternative(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.locator('button[data-lesson-id="sentence-building"]').click()
    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    for position, token in enumerate(["a", "b", "c", "d"]):
        page.locator(".learning-order-select").nth(position).select_option(token)
    page.locator("#learning-submit").click()
    page.locator("#learning-reflection").fill("I built a small web application.")
    page.locator("#learning-submit").click()
    page.locator("#learning-feedback button").click()

    page.locator('button[data-lesson-id="listening-for-details"]').click()
    page.locator(".learning-listening-controls").wait_for(state="visible")
    transcript = page.locator(".learning-transcript")
    assert transcript.is_hidden()
    page.locator(".learning-listening-controls button").nth(1).click()
    assert transcript.is_visible()
    assert "input validation" in transcript.inner_text().lower()
    assert "text alternative" in page.locator(".learning-listening-controls").inner_text().lower()
