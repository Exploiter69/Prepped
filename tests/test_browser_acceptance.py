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


def open_lesson_in_browser(page, lesson_id: str) -> None:
    btn = page.locator(f'button[data-lesson-id="{lesson_id}"]').first
    btn.wait_for(state="attached")
    if not btn.is_visible():
        # Switch to the track tab containing this lesson, then expand its unit disclosure if collapsed.
        track_id = page.evaluate(
            """(id) => {
              const el = document.querySelector(`button[data-lesson-id="${id}"]`);
              return el?.closest('.learning-track')?.dataset?.trackId || null;
            }""",
            lesson_id,
        )
        if track_id:
            tab = page.locator(f'#learning-track-tabs button[data-track-id="{track_id}"]')
            if tab.count():
                tab.click()
        unit_id = page.evaluate(
            """(id) => {
              const el = document.querySelector(`button[data-lesson-id="${id}"]`);
              return el?.closest('details.learning-unit')?.dataset?.unitId || null;
            }""",
            lesson_id,
        )
        if unit_id:
            unit = page.locator(f'details.learning-unit[data-unit-id="{unit_id}"]')
            if unit.count() and not unit.evaluate("(el) => el.open"):
                unit.locator("summary").click()
    btn.click()


def complete_lesson_in_browser(page, lesson_id: str, answers: list[str | list[str]]) -> None:
    open_lesson_in_browser(page, lesson_id)
    page.locator("#learning-runner").wait_for(state="visible")
    for index, answer in enumerate(answers, start=1):
        if isinstance(answer, list):
            for position, token in enumerate(answer):
                page.locator(".learning-order-select").nth(position).select_option(token)
        elif page.locator('input[name="learning-choice"]').count():
            page.locator(f'input[name="learning-choice"][value="{answer}"]').check()
        else:
            page.locator("#learning-reflection").fill(answer)
        page.locator("#learning-submit").click()
        if index < len(answers):
            page.wait_for_function(
                "(expected) => document.querySelector('#learning-exercise-count').textContent === expected",
                arg=f"Exercise {index + 1} of {len(answers)}",
            )
        else:
            page.wait_for_function(
                "() => !document.querySelector('#learning-feedback').classList.contains('hidden')"
            )


def test_dashboard_is_the_landing_view_and_uses_real_learning_data(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")
    page.wait_for_function("() => document.querySelector('#dashboard-track-description').textContent !== 'Loading your recommended learning path…'")
    assert page.locator("#dashboard-hero-title").is_visible()
    assert page.locator("#dashboard-path-preview .dashboard-lesson").count() > 0
    assert page.locator("#home-toggle").get_attribute("aria-current") == "page"
    page.locator("#learning-toggle").click()
    page.locator("#learning-view").wait_for(state="visible")
    assert not page.locator("#dashboard-view").is_visible()


def test_learning_path_summary_track_progress_and_guided_step_indicator(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )

    assert page.locator("#learning-summary-completed").text_content() == "0"
    assert page.locator("#learning-summary-skills").text_content().endswith("/ 14")
    assert page.locator(".learning-track-progressbar[role='progressbar']").count() == 3

    open_lesson_in_browser(page, "sentence-building")
    page.locator("#learning-runner").wait_for(state="visible")
    progress = page.locator("#learning-step-progress")
    assert progress.get_attribute("role") == "progressbar"
    assert progress.get_attribute("aria-valuenow") == "0"
    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 2 of 3'"
    )
    assert progress.get_attribute("aria-valuenow") == "33"
    assert "Step 2 of 3" in page.locator("#learning-step-label").text_content()


def test_profile_setup_edit_cancel_save_and_reload(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.wait_for_function(
        "() => document.querySelector('#profile-save-status').textContent === 'Not set up'"
    )
    page.locator("#profile-nav-toggle").click()
    page.locator("#profile-view").wait_for(state="visible")

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
    page.locator("#profile-nav-toggle").click()
    page.locator("#profile-view").wait_for(state="visible")
    assert "English fluency" in page.locator("#profile-summary").inner_text()
    assert "Year 2" in page.locator("#profile-summary").inner_text()

    if form.is_hidden():
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
    page.locator("#profile-nav-toggle").click()
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
    page.locator("#practice-toggle").click()
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

    page.locator("#question-feedback button").filter(has_text="Save a learning note").first.click()
    page.locator("#memory-view").wait_for(state="visible")
    page.locator("#memory-editor-modal").wait_for(state="visible")
    assert page.locator("#memory-source-type").input_value() == "practice"
    assert "Attempt 1" in page.locator("#memory-source-title").input_value()
    assert "I built a small API" in page.locator("#memory-source-excerpt").input_value()
    saved_front = page.locator("#memory-front").input_value().strip()
    assert saved_front
    page.locator("#memory-form-submit").click()
    page.wait_for_function(
        "(expected) => document.querySelector('#memory-items').textContent.includes(expected)",
        arg=saved_front,
    )

    page.locator("#history-toggle").click()
    page.locator("#history-view").wait_for(state="visible")
    page.locator('#history-tabs button[data-history-tab="sessions"]').click()
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
    page.locator("#learning-view .learn-secondary-disclosure summary").click()
    assert "active" in page.locator("#learning-skill-list").inner_text().lower()

    open_lesson_in_browser(page, "sentence-building")
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
    assert page.locator("#learning-outcomes li").count() >= 1
    assert "Recognise a complete sentence" in page.locator("#learning-outcomes").inner_text()

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
    next_lesson = page.locator("#learning-feedback button").filter(has_text="Next lesson: Shape a sentence for clarity")
    assert next_lesson.is_visible()
    next_lesson.click()
    page.wait_for_function(
        "() => document.querySelector('#learning-runner-title').textContent.includes('Shape a sentence for clarity')"
    )
    page.locator("#learning-exit").click()
    disclosure = page.locator("#learning-view .learn-secondary-disclosure")
    if not disclosure.evaluate("(el) => el.open"):
        disclosure.locator("summary").click()
    assert "Lessons completed" in page.locator("#learning-progress").inner_text()


def test_listening_lesson_has_playback_and_revealed_text_alternative(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    open_lesson_in_browser(page, "sentence-building")
    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    for position, token in enumerate(["a", "b", "c", "d"]):
        page.locator(".learning-order-select").nth(position).select_option(token)
    page.locator("#learning-submit").click()
    page.locator("#learning-reflection").fill("I built a small web application.")
    page.locator("#learning-submit").click()
    page.get_by_role("button", name="Back to lesson list").click()

    open_lesson_in_browser(page, "listening-for-details")
    page.locator(".learning-listening-controls").wait_for(state="visible")
    transcript = page.locator(".learning-transcript")
    assert transcript.is_hidden()
    page.get_by_role("button", name="Show text alternative").click()
    assert transcript.is_visible()
    assert "input validation" in transcript.inner_text().lower()
    assert "text alternative" in page.locator(".learning-listening-controls").inner_text().lower()


def test_baseline_check_records_responses_without_a_proficiency_score(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills') && document.querySelector('#learning-diagnostic-status').textContent === 'Not started'"
    )
    page.locator("#learning-diagnostic-start").click()
    page.locator("#learning-runner").wait_for(state="visible")
    assert "Record your starting point" in page.locator("#learning-runner-title").inner_text()

    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    for position, token in enumerate(["a", "b", "c"]):
        page.locator(".learning-order-select").nth(position).select_option(token)
    page.locator("#learning-submit").click()
    page.get_by_role("button", name="Show text alternative").click()
    page.locator('input[name="learning-choice"][value="c"]').check()
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 4 of 4'"
    )
    page.locator("#learning-reflection").fill("I built a small task tracker and checked the form with test inputs.")
    page.locator("#learning-submit").click()

    page.wait_for_function(
        "() => document.querySelector('#learning-diagnostic-status').textContent.includes('Completed')"
    )
    feedback = page.locator("#learning-feedback").inner_text().lower()
    assert "not automatically graded" in feedback
    assert "score" not in feedback
    page.get_by_role("button", name="Back to lesson list").click()
    disclosure = page.locator("#learning-view .learn-secondary-disclosure")
    if not disclosure.evaluate("(el) => el.open"):
        disclosure.locator("summary").click()
    assert "Baseline checks completed" in page.locator("#learning-progress").inner_text()
    assert page.locator("#learning-diagnostic-history button").count() == 1
    page.locator("#learning-diagnostic-history button").click()
    assert "Record your starting point" in page.locator("#learning-runner-title").inner_text()


def test_lessons_with_uncompleted_prerequisites_are_still_openable(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    open_lesson_in_browser(page, "speaking-opinions")
    page.locator("#learning-runner").wait_for(state="visible")
    assert "Express an opinion" in page.locator("#learning-runner-title").inner_text()


def test_english_track_exposes_complete_phase_c_units(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    page.locator('#learning-track-tabs button[data-track-id="english-foundations"]').click()
    track = page.locator('.learning-track[data-track-id="english-foundations"]')
    assert track.locator("details.learning-unit").count() == 6
    # Only the first unfinished unit is expanded by default to keep Learn concise.
    assert track.locator("details.learning-unit[open]").count() == 1
    assert track.locator(".learning-unit-outcomes li").count() >= 12
    for unit_idx in range(track.locator("details.learning-unit").count()):
        unit = track.locator("details.learning-unit").nth(unit_idx)
        if not unit.evaluate("(el) => el.open"):
            unit.locator("summary").click()
    for title in [
        "Build a clear sentence", "Shape a sentence for clarity", "Grammar in context",
        "Ask clear questions", "Choose useful words in context", "Use useful study and project phrases",
        "Listen for the key detail", "Follow a short conversation", "Give a clear short response",
        "Express an opinion and handle a follow-up", "Listen, repeat, and self-review",
    ]:
        assert track.locator(".learning-card h6", has_text=title).is_visible()


def test_pronunciation_lesson_supports_replay_text_and_unscored_self_review(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    complete_lesson_in_browser(page, "sentence-building", [
        "b", ["a", "b", "c", "d"], "I tested the registration form."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "sentence-shaping", [
        "a", ["a", "b", "c"], "Because the server did not respond, I could not access the page."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "speaking-structured", [
        "I worked on a form and added validation.",
        "First I opened the form, then I checked the inputs.",
        "I checked the form with invalid inputs and observed the validation message.",
        "The first version is ready, two issues were found, and fixes are planned.",
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "speaking-opinions", [
        "Documentation explains the full interface; a small example reveals practical behaviour. I would try an example for a simple tool.",
        "I prefer trying a small example first because it helps me see the tool in action.",
        "Reading documentation can be useful when the tool has complex setup or safety requirements.",
        "Could you please rephrase the question?",
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    open_lesson_in_browser(page, "pronunciation-self-review")
    page.locator(".learning-listening-controls").wait_for(state="visible")
    assert page.get_by_role("button", name="Play model phrase").is_visible()
    page.get_by_role("button", name="Show phrase text").click()
    phrase = page.locator(".learning-transcript")
    assert phrase.is_visible()
    assert "I tested the application" in phrase.inner_text()
    assert page.get_by_role("button", name="Record spoken response").is_visible()
    page.locator("#learning-reflection").fill("I practised at a comfortable pace.")
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 2 of 3'"
    )
    page.get_by_role("button", name="Show phrase text").click()
    page.locator("#learning-reflection").fill("I paused before please.")
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 3 of 3'"
    )
    page.locator("#learning-reflection").fill("I want to practise word endings.")
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => !document.querySelector('#learning-feedback').classList.contains('hidden')"
    )
    feedback = page.locator("#learning-feedback").inner_text().lower()
    assert "does not measure pronunciation" in feedback
    assert "no pronunciation score" in feedback


def test_listening_conversation_has_replay_controls_and_accessible_text(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    complete_lesson_in_browser(page, "sentence-building", [
        "b", ["a", "b", "c", "d"], "I tested the registration form."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "listening-for-details", [
        "b", "b", "The completed task was input validation; deployment testing remains pending."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    open_lesson_in_browser(page, "listening-conversations")
    page.locator(".learning-listening-controls").wait_for(state="visible")
    assert page.get_by_role("button", name="Play spoken message").is_visible()
    page.get_by_role("button", name="Show text alternative").click()
    assert "Riya:" in page.locator(".learning-transcript").inner_text()
    assert "Arjun:" in page.locator(".learning-transcript").inner_text()


def test_vocabulary_lesson_submits_contextual_choices_and_learner_example(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    complete_lesson_in_browser(page, "sentence-building", [
        "b", ["a", "b", "c", "d"], "I tested the registration form."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "vocabulary-in-context", [
        "a", "b", "Original: I did a lot of work. Revised: I completed several tasks."
    ])
    feedback = page.locator("#learning-feedback").inner_text()
    assert "carry out research" in feedback.lower()
    assert "I completed several tasks" in feedback
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "phrases-for-study", [
        "a", "b", "a", "I carried out a test of the login form."
    ])
    assert "carry out tests" in page.locator("#learning-feedback").inner_text().lower()


def test_grammar_and_question_formation_units_complete_in_the_browser(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    complete_lesson_in_browser(page, "sentence-building", [
        "b", ["a", "b", "c", "d"], "I tested the registration form."
    ])
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "grammar-in-context", [
        "b", "a", "Yesterday, I tested the API.", "a", "b",
        "Yesterday, she went to the lab and checked the results.",
    ])
    assert "responsible for" in page.locator("#learning-feedback").inner_text()
    page.get_by_role("button", name="Back to lesson list").click()
    complete_lesson_in_browser(page, "question-formation", [
        "a", "b", "Could you clarify the expected response?"
    ])
    assert "does" in page.locator("#learning-feedback").inner_text().lower()


def test_memory_create_edit_and_review_flow_in_browser(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#memory-toggle").click()
    page.locator("#memory-view").wait_for(state="visible")
    page.locator("#memory-open-editor").click()
    page.locator("#memory-editor-modal").wait_for(state="visible")
    page.locator("#memory-front").fill("in the long run")
    page.locator("#memory-back").fill("Over a long period of time.")
    page.locator("#memory-form button[type='submit']").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('in the long run')"
    )
    assert "Active cards" in page.locator("#memory-stats").inner_text()
    page.locator("#memory-open-editor").click()
    page.locator("#memory-editor-modal").wait_for(state="visible")
    page.locator("#memory-front").fill("  IN   THE LONG RUN ")
    page.locator("#memory-back").fill("A duplicate attempt.")
    page.locator("#memory-form-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-form-title').textContent === 'Edit saved item'"
    )
    assert "already exists" in page.locator("#memory-status").inner_text()
    page.locator("#memory-form-cancel").click()
    page.locator("#memory-review button").filter(has_text="Show answer").click()
    assert "Over a long period of time." in page.locator("#memory-review").inner_text()
    page.locator("#memory-review button").filter(has_text="Good").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-review').textContent.includes('clear for now')"
    )
    assert "Reviews completed" in page.locator("#memory-stats").inner_text()
    page.locator("#memory-items button").filter(has_text="Review history").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('GOOD')"
    )

    page.locator("#memory-items button").filter(has_text="Edit").click()
    page.locator("#memory-front").fill("over time")
    page.locator("#memory-form-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('over time')"
    )
    page.locator("#memory-items button").filter(has_text="Suspend").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('Paused')"
    )
    page.locator("#memory-items button").filter(has_text="Resume").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('Active')"
    )
    page.locator("#memory-items button").filter(has_text="Dismiss").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('Dismissed')"
    )
    page.locator("#memory-items button").filter(has_text="Restore").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('Active')"
    )


def test_lesson_memory_suggestion_requires_explicit_save_and_keeps_source(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    complete_lesson_in_browser(
        page,
        "sentence-building",
        ["b", ["a", "b", "c", "d"], "I built a small study planner."],
    )
    page.locator("#learning-feedback button").filter(has_text="Save a learning note").first.click()
    assert page.locator("#memory-type").input_value() == "correction"
    assert page.locator("#memory-front").input_value() == "Which option is a complete sentence?"
    assert page.locator("#memory-source-title").input_value() == "Build a clear sentence"
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('No saved items yet')"
    )
    assert "No saved items yet" in page.locator("#memory-items").inner_text()
    assert page.locator("#memory-form-cancel").inner_text() == "Discard suggestion"
    page.locator("#memory-form-cancel").click()
    assert "No saved items yet" in page.locator("#memory-items").inner_text()
    page.locator("#learning-toggle").click()
    page.locator("#learning-feedback button").filter(has_text="Save a learning note").first.click()
    page.locator("#memory-editor-modal").wait_for(state="visible")
    page.locator("#memory-form-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('Which option is a complete sentence?')"
    )
    assert "Build a clear sentence" in page.locator("#memory-items").inner_text()


def test_career_studio_voice_optional_text_interview_feedback_and_retry(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card").filter(has_text="Project Explanation Studio").get_by_role("button").click()
    page.locator("#career-setup").wait_for(state="visible")
    page.locator("#career-difficulty").select_option("challenging")
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    assert "What problem does it address" in page.locator("#career-prompt-title").inner_text()

    for turn in range(8):
        page.locator("#career-answer").fill(
            f"I built a project and tested the feature. For example, a student can use it. "
            f"Because the first approach had a limitation, I changed it. Evidence {turn}."
        )
        page.locator("#career-submit").click()
        if turn < 7:
            page.wait_for_function(
                "(previous) => document.querySelector('#career-answer').value === '' && document.querySelector('#career-prompt-title').textContent.length > 0",
                arg=turn,
            )
    page.locator("#career-review").wait_for(state="visible")
    assert "not an expert interview rating" in page.locator("#career-review-disclaimer").inner_text()
    assert page.locator(".career-review-card").count() == 8
    assert "Suggested next steps" in page.locator("#career-next-steps").inner_text()
    page.locator("#career-retry").click()
    page.locator("#career-active").wait_for(state="visible")
    assert page.locator("#career-answer").input_value() == ""
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#career-exit").click()
    page.locator("#career-history-stage").wait_for(state="visible")
    page.locator("#career-history-list button").filter(has_text="Open").nth(1).click()
    page.locator("#career-review").wait_for(state="visible")
    page.locator(".career-review-card button").first.click()
    page.locator("#memory-view").wait_for(state="visible")
    page.locator("#memory-editor-modal").wait_for(state="visible")
    assert page.locator("#memory-type").input_value() == "example"
    assert page.locator("#memory-front").input_value()
    assert page.locator("#memory-back").input_value()
    assert "No saved items yet" in page.locator("#memory-items").inner_text()
    page.locator("#memory-form-cancel").click()
    assert "No saved items yet" in page.locator("#memory-items").inner_text()


def test_career_interview_can_resume_at_saved_followup(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card").filter(has_text="HR & Behavioural Interview Studio").get_by_role("button").click()
    page.locator("#career-start").click()
    page.locator("#career-answer").fill("I worked with a team to complete a class project.")
    page.locator("#career-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#career-turn-label').textContent.includes('FOLLOW-UP')"
    )
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#career-exit").click()
    page.locator("#career-history-list button").filter(has_text="Open").first.click()
    page.wait_for_function(
        "() => document.querySelector('#career-turn-label').textContent.includes('FOLLOW-UP')"
    )
    resumed_prompt = page.locator("#career-prompt-title").inner_text().lower()
    assert resumed_prompt.startswith("which specific experience")
    assert "strength you mentioned" in resumed_prompt


def test_progress_goals_and_backup_restore_in_browser(local_app_url: str, browser_page, tmp_path: Path) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#progress-toggle").click()
    page.locator("#progress-status").wait_for()
    page.wait_for_function("() => document.querySelector('#progress-status').textContent.startsWith('Updated')")
    assert page.locator("#progress-summary .progress-stat").count() == 6
    recommendation = page.locator("#progress-recommendations .progress-row").first
    if recommendation.count():
        recommendation.get_by_role("button", name="Dismiss").click()
        page.wait_for_function("() => document.querySelector('#progress-dismissed-toggle').textContent.includes('(1)')")
        page.locator("#progress-dismissed-toggle").click()
        assert page.locator("#progress-dismissed-toggle").get_attribute("aria-expanded") == "true"
        assert page.locator("#progress-dismissed-recommendations").is_visible()
        page.locator("#progress-dismissed-recommendations").get_by_role("button", name="Restore suggestion").first.click()
        page.wait_for_function("() => document.querySelector('#progress-dismissed-toggle').textContent.includes('(0)')")

    page.locator('#progress-tabs button[data-progress-tab="plan"]').click()
    page.locator("#goal-title").fill("Complete two lessons")
    page.locator("#goal-type").select_option("lessons_completed")
    page.locator("#goal-target").fill("2")
    page.locator("#goal-form button[type='submit']").click()
    page.locator("#progress-goals").get_by_text("Complete two lessons", exact=True).wait_for()
    assert "Complete two lessons" in page.locator("#progress-goals").inner_text()
    assert "0 / 2" in page.locator("#progress-goals").inner_text()
    page.locator("#progress-goals").get_by_role("button", name="Edit").click()
    page.locator("#goal-title").fill("Complete two lessons this month")
    page.locator("#goal-form button[type='submit']").click()
    page.locator("#progress-goals").get_by_text("Complete two lessons this month", exact=True).wait_for()
    assert "Complete two lessons this month" in page.locator("#progress-goals").inner_text()
    page.locator("#progress-goals").get_by_role("button", name="Archive").click()
    page.locator("#progress-goals").get_by_text("No active goals yet", exact=False).wait_for()
    assert "No active goals yet" in page.locator("#progress-goals").inner_text()
    page.locator("#goal-archive-toggle").click()
    page.locator("#progress-archived-goals").get_by_text("Complete two lessons this month", exact=True).wait_for()
    assert "Complete two lessons this month" in page.locator("#progress-archived-goals").inner_text()
    page.locator("#progress-archived-goals").get_by_role("button", name="Restore").click()
    page.locator("#progress-goals").get_by_text("Complete two lessons this month", exact=True).wait_for()
    assert "Complete two lessons this month" in page.locator("#progress-goals").inner_text()

    page.locator('#progress-tabs button[data-progress-tab="data"]').click()
    with page.expect_download() as download_info:
        page.locator("#data-export").click()
    download = download_info.value
    backup_path = tmp_path / "prepped-backup.json"
    download.save_as(backup_path)
    assert backup_path.stat().st_size > 0

    before_reload = page.evaluate("performance.timeOrigin")
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#data-import").set_input_files(str(backup_path))
    page.wait_for_function("(before) => performance.timeOrigin > before", arg=before_reload, timeout=10000)
    page.locator("#progress-toggle").click()
    page.wait_for_function("() => document.querySelector('#progress-status').textContent.startsWith('Updated')")
    page.locator('#progress-tabs button[data-progress-tab="plan"]').click()
    assert "Complete two lessons this month" in page.locator("#progress-goals").inner_text()


def test_progress_navigation_and_security_headers_are_accessible(local_app_url: str, browser_page) -> None:
    page = browser_page
    response = page.goto(local_app_url)
    assert response is not None
    assert response.headers.get("content-security-policy")
    assert response.headers.get("x-content-type-options") == "nosniff"
    toggle = page.locator("#progress-toggle")
    assert toggle.get_attribute("aria-controls") == "progress-view"
    toggle.click()
    assert toggle.get_attribute("aria-current") == "page"
    assert page.locator("#progress-view").is_visible()
    assert page.locator(".nav-button[aria-current='page']").count() == 1
    page.locator("#learning-toggle").click()
    assert toggle.get_attribute("aria-current") is None
    assert page.locator("#learning-toggle").get_attribute("aria-current") == "page"
    assert page.locator("#learning-view").is_visible()



def test_keyboard_navigation_exposes_focus_and_profile_labels(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    # Start from a known document focus; Chromium may otherwise retain its
    # initial page focus state, making the first Tab nondeterministic.
    page.evaluate("""() => {
      document.activeElement.blur?.();
      document.body.setAttribute("tabindex", "-1");
      document.body.focus();
    }""")

    # The Stage 8 skip link is the first keyboard stop and sends focus to main.
    page.keyboard.press("Tab")
    assert page.locator(".skip-link").evaluate(
        "(element) => document.activeElement === element"
    )
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid"
    page.keyboard.press("Enter")
    assert page.locator("#main-content").evaluate(
        "(element) => document.activeElement === element"
    )

    # Restart document-order traversal to verify header navigation separately.
    # Tab from the focused main landmark proceeds into main content, not backward
    # to the header; the wordmark follows the skip link in document order.
    page.evaluate("""() => {
      document.activeElement.blur?.();
      document.body.focus();
    }""")
    page.keyboard.press("Tab")  # skip link
    page.keyboard.press("Tab")  # wordmark
    assert page.evaluate("document.activeElement.classList.contains('wordmark')")
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid"

    # Reference order: Today, Practice, Learn, Career, Memory, Progress.
    # After focusing the wordmark, five Tab presses reach Memory.
    for _ in range(5):
        page.keyboard.press("Tab")
    assert page.locator("#memory-toggle").evaluate(
        "(element) => document.activeElement === element"
    )
    page.keyboard.press("Tab")
    assert page.locator("#progress-toggle").evaluate(
        "(element) => document.activeElement === element"
    )
    page.keyboard.press("Tab")
    assert page.locator("#profile-nav-toggle").evaluate(
        "(element) => document.activeElement === element"
    )
    page.keyboard.press("Enter")
    assert page.locator("#profile-view").is_visible()
    assert page.locator("#profile-form").is_visible()
    assert page.locator("#profile-edit-toggle").get_attribute("aria-expanded") == "true"
    assert page.locator("#profile-name").evaluate(
        "(element) => document.activeElement === element"
    )
    assert page.get_by_label("Name (optional)").count() == 1
    assert page.get_by_label("Current study year").count() == 1
    assert page.get_by_label("Primary learning goal").count() == 1


def test_mobile_layout_has_no_horizontal_page_overflow(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(local_app_url)

    def assert_no_horizontal_overflow() -> None:
        dimensions = page.evaluate(
            "() => ({width: window.innerWidth, scrollWidth: document.documentElement.scrollWidth})"
        )
        assert dimensions["scrollWidth"] <= dimensions["width"], dimensions

    assert_no_horizontal_overflow()
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    assert_no_horizontal_overflow()
    page.locator("#career-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#career-status').textContent.toLowerCase().includes('studios')"
    )
    assert_no_horizontal_overflow()
    page.locator("#progress-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#progress-status').textContent.startsWith('Updated')"
    )
    page.wait_for_function(
        "() => document.querySelector('#intelligence-status').textContent.startsWith('Evidence updated')"
    )
    assert_no_horizontal_overflow()


def _deferred_microphone_script() -> str:
    return """
    window.__stoppedTracks = 0;
    window.__createdRecorders = 0;
    Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
      configurable: true,
      value: () => new Promise(resolve => {
        window.__resolveMicrophone = () => resolve({
          getTracks: () => [{ stop: () => { window.__stoppedTracks += 1; } }]
        });
      })
    });
    window.MediaRecorder = class {
      constructor() { window.__createdRecorders += 1; this.state = "inactive"; }
      static isTypeSupported() { return false; }
    };
    """


def _mock_available_voice_status(page) -> None:
    page.route(
        "**/api/voice/status",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"stt":{"available":true,"engine":"vosk","detail":"Mock speech engine ready."},"tts":{"available":false}}',
        ),
    )


def test_learning_discards_late_microphone_permission_after_navigation(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_deferred_microphone_script())
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    open_lesson_in_browser(page, "sentence-building")
    page.locator('input[name="learning-choice"][value="b"]').check()
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 2 of 3'"
    )
    for position, token in enumerate(["a", "b", "c", "d"]):
        page.locator(".learning-order-select").nth(position).select_option(token)
    page.locator("#learning-submit").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-exercise-count').textContent === 'Exercise 3 of 3'"
    )

    page.get_by_role("button", name="Record spoken response").click()
    page.wait_for_function("() => typeof window.__resolveMicrophone === 'function'")
    page.evaluate("window.PreppedApp.showView('progress-view')")
    page.evaluate("window.__resolveMicrophone()")
    page.wait_for_function("() => window.__stoppedTracks === 1")

    assert page.evaluate("window.__createdRecorders") == 0
    assert page.locator("#progress-view").is_visible()


def test_career_discards_late_microphone_permission_after_navigation(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_deferred_microphone_script())
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card button").first.click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")

    page.locator("#career-record").click()
    page.wait_for_function("() => typeof window.__resolveMicrophone === 'function'")
    page.locator("#learning-toggle").click()
    page.evaluate("window.__resolveMicrophone()")
    page.wait_for_function("() => window.__stoppedTracks === 1")

    assert page.evaluate("window.__createdRecorders") == 0
    assert page.locator("#learning-view").is_visible()


def test_adaptive_learning_workspace_renders_evidence_and_daily_weekly_plans(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#progress-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#intelligence-status').textContent.startsWith('Evidence updated')"
    )
    assert page.locator("#intelligence-recommendations").is_visible()
    page.locator('#progress-tabs button[data-progress-tab="skills"]').click()
    assert page.locator("#intelligence-skills .intelligence-skill").count() > 0

    page.locator('#progress-tabs button[data-progress-tab="plan"]').click()
    page.locator("#intelligence-generate-day").click()
    page.wait_for_function(
        "() => document.querySelector('#intelligence-plan-date-label').textContent.includes('planned min')"
    )
    assert page.locator("#intelligence-plan-items .intelligence-plan-item").count() > 0

    page.locator("#intelligence-generate-week").click()
    page.wait_for_function(
        "() => document.querySelectorAll('#intelligence-week .intelligence-week-day').length === 7"
    )
    assert page.locator("#intelligence-week .intelligence-week-day").count() == 7
    page.locator('#progress-tabs button[data-progress-tab="data"]').click()
    assert page.locator("#intelligence-activity .progress-day").count() == 30



def test_career_prompt_audio_request_is_aborted_when_leaving_workspace(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.add_init_script("""
        (() => {
          const originalFetch = window.fetch.bind(window);
          window.fetch = (input, init = {}) => {
            if (String(input).includes("/api/voice/tts")) {
              window.__careerTtsSignal = init.signal;
              return new Promise((resolve, reject) => {
                init.signal?.addEventListener("abort", () => {
                  reject(new DOMException("Aborted", "AbortError"));
                }, { once: true });
                window.__resolveCareerTts = () => resolve(new Response(new Blob(["wav"]), { status: 200 }));
              });
            }
            return originalFetch(input, init);
          };
        })();
    """)
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card button").first.click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    page.locator("#career-speak").click()
    page.wait_for_function("() => window.__careerTtsSignal !== undefined")
    page.locator("#learning-toggle").click()
    assert page.evaluate("window.__careerTtsSignal.aborted") is True
    assert page.locator("#learning-view").is_visible()


def test_career_review_can_add_next_practice_to_adaptive_plan(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card button").first.click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    original_prompt = page.locator("#career-prompt-title").inner_text()
    page.locator("#career-simpler-prompt").click()
    assert page.locator("#career-prompt-title").inner_text() != original_prompt
    page.locator("#career-clarify-prompt").click()
    assert page.locator("#career-prompt-help").is_visible()
    assert page.locator("#career-prompt-help").inner_text()
    page.locator("#career-simpler-prompt").click()
    assert page.locator("#career-prompt-title").inner_text() == original_prompt

    for attempt_label in ("first", "second"):
        for index in range(4):
            page.locator("#career-answer").fill(
                f"For example, I built and tested the {attempt_label} project feature {index} because it addressed a user need. "
                "The result was verified with a repeatable test."
            )
            page.locator("#career-submit").click()
            page.wait_for_function(
                "() => document.querySelector('#career-turn-label').textContent.includes('FOLLOW-UP')"
            )
            page.locator("#career-answer").fill(
                f"For example, I checked the {attempt_label} result because the user journey mattered, then tested the change."
            )
            page.locator("#career-submit").click()
            if index < 3:
                page.wait_for_function(
                    "() => document.querySelector('#career-turn-label').textContent.includes('MAIN QUESTION')"
                )
        page.locator("#career-review").wait_for(state="visible")
        if attempt_label == "first":
            page.locator("#career-retry").click()
            page.locator("#career-active").wait_for(state="visible")

    assert page.locator("#career-attempt-comparison").is_visible()
    comparison_text = page.locator("#career-attempt-comparison").inner_text()
    assert "first project feature" in comparison_text
    assert "second project feature" in comparison_text
    assert "not a measured improvement" in comparison_text.lower()
    page.evaluate("""async () => {
      const now = new Date();
      const date = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
      await fetch("/api/intelligence/plan/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_date: date, available_minutes: 180 })
      });
    }""")
    page.locator("#career-add-plan").click()
    page.wait_for_function(
        """() => document.querySelector('#career-status').textContent.includes("today's plan")"""
    )
    plan = page.evaluate("""async () => {
      const now = new Date();
      const date = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("-");
      const response = await fetch("/api/intelligence/plan?plan_date=" + date);
      return (await response.json()).plan;
    }""")
    assert any(
        item["item_type"] == "career_practice"
        and item["target_id"] == "project-explanation"
        for item in plan["items"]
    )


def test_project_prompt_audio_request_is_aborted_when_leaving_practice(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.add_init_script("""
        (() => {
          const originalFetch = window.fetch.bind(window);
          window.fetch = (input, init = {}) => {
            if (String(input).includes("/api/voice/status")) {
              return Promise.resolve(new Response(JSON.stringify({
                stt: { kind: "stt", engine: "fake", available: true, detail: "Fake STT ready." },
                tts: { kind: "tts", engine: "fake", available: true, detail: "Fake TTS ready." },
                limits: { max_recording_seconds: 60, max_audio_bytes: 12582912, max_tts_characters: 1200 }
              }), { status: 200, headers: { "Content-Type": "application/json" } }));
            }
            if (String(input).includes("/api/voice/tts")) {
              window.__practiceTtsSignal = init.signal;
              return new Promise((resolve, reject) => {
                init.signal?.addEventListener("abort", () => {
                  reject(new DOMException("Aborted", "AbortError"));
                }, { once: true });
                window.__resolvePracticeTts = () => resolve(new Response(new Blob(["wav"]), { status: 200 }));
              });
            }
            return originalFetch(input, init);
          };
        })();
    """)
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")
    page.locator("#tts-play-button").click()
    page.wait_for_function("() => window.__practiceTtsSignal !== undefined")
    page.locator("#career-toggle").click()
    assert page.evaluate("window.__practiceTtsSignal.aborted") is True
    assert page.locator("#career-view").is_visible()


def _recording_and_deferred_transcription_script(signal_name: str) -> str:
    return f"""
    (() => {{
      Object.defineProperty(navigator.mediaDevices, "getUserMedia", {{
        configurable: true,
        value: async () => ({{ getTracks: () => [{{ stop() {{}} }}] }})
      }});
      window.MediaRecorder = class {{
        constructor() {{ this.state = "inactive"; this.mimeType = "audio/webm"; this.listeners = {{}}; }}
        static isTypeSupported() {{ return true; }}
        addEventListener(name, callback) {{ (this.listeners[name] ||= []).push(callback); }}
        dispatch(name, event = {{}}) {{
          for (const callback of this.listeners[name] || []) callback(event);
          this["on" + name]?.(event);
        }}
        start() {{ this.state = "recording"; }}
        stop() {{
          this.state = "inactive";
          this.dispatch("dataavailable", {{ data: new Blob(["captured-audio"], {{ type: "audio/webm" }}) }});
          this.dispatch("stop");
        }}
      }};
      const originalFetch = window.fetch.bind(window);
      window.fetch = (input, init = {{}}) => {{
        if (String(input).includes("/api/voice/transcribe")) {{
          window.{signal_name} = init.signal;
          return new Promise((resolve, reject) => {{
            init.signal?.addEventListener("abort", () => {{
              reject(new DOMException("Aborted", "AbortError"));
            }}, {{ once: true }});
          }});
        }}
        return originalFetch(input, init);
      }};
    }})();
    """


def test_career_transcription_request_is_aborted_when_leaving_workspace(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_recording_and_deferred_transcription_script("__careerSttSignal"))
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator(".career-studio-card button").first.click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    page.locator("#career-record").click()
    page.wait_for_function("() => document.querySelector('#career-voice-status').textContent.startsWith('Recording')")
    page.locator("#career-stop-record").click()
    page.wait_for_function("() => window.__careerSttSignal !== undefined")
    page.locator("#learning-toggle").click()
    assert page.evaluate("window.__careerSttSignal.aborted") is True
    assert page.locator("#learning-view").is_visible()


def test_project_transcription_request_is_aborted_when_leaving_practice(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_recording_and_deferred_transcription_script("__practiceSttSignal"))
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")
    page.locator("#record-button").click()
    page.wait_for_function("() => document.querySelector('#record-status').textContent.startsWith('Recording')")
    page.locator("#stop-recording-button").click()
    page.wait_for_function("() => window.__practiceSttSignal !== undefined")
    page.locator("#career-toggle").click()
    assert page.evaluate("window.__practiceSttSignal.aborted") is True
    assert page.locator("#career-view").is_visible()


def test_practice_room_redesign_has_accessible_progress_and_editable_draft(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    progress = page.locator("#practice-progress-track")
    assert progress.get_attribute("role") == "progressbar"
    assert progress.get_attribute("aria-valuenow") == "0"
    assert progress.get_attribute("aria-valuemax") == "5"
    assert page.locator("#recording-visualizer span").count() == 24
    assert page.locator("#answer-input").is_visible()
    assert page.locator("#practice-privacy summary").inner_text() == "How your voice and answers are handled"

    page.locator("#answer-input").fill("I built a small API and verified it with automated tests.")
    assert page.locator("#response-draft-state").inner_text() == "Draft in progress · not saved"
    page.locator("#submit-button").click()
    page.wait_for_function("() => document.querySelector('#practice-progress-track').getAttribute('aria-valuenow') === '1'")
    assert page.locator("#practice-progress-track").get_attribute("aria-valuetext") == "1 of 5 questions completed"


def test_practice_visualizer_is_active_only_during_microphone_capture(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_recording_and_deferred_transcription_script("__practiceVisualiserSignal"))
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    page.locator("#record-button").click()
    page.wait_for_function("() => document.querySelector('#record-status').textContent.startsWith('Recording')")
    assert "is-active" in (page.locator("#recording-visualizer").get_attribute("class") or "")
    page.locator("#stop-recording-button").click()
    page.wait_for_function("() => window.__practiceVisualiserSignal !== undefined")
    assert "is-active" not in (page.locator("#recording-visualizer").get_attribute("class") or "")
    assert page.locator("#record-status").inner_text().startswith("Transcribing locally")


def test_groq_audio_disclosure_is_visible_before_microphone_capture(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.route(
        "**/api/voice/status",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"stt":{"available":true,"engine":"groq-whisper","detail":"Groq ready."},"tts":{"available":false}}',
        ),
    )
    page.add_init_script("""
        (() => {
          window.__captureRequests = 0;
          const media = navigator.mediaDevices;
          if (!media?.getUserMedia) return;
          const original = media.getUserMedia.bind(media);
          media.getUserMedia = (...args) => {
            window.__captureRequests += 1;
            return original(...args);
          };
        })();
    """)
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    page.wait_for_function("() => document.querySelector('#privacy-note').textContent.includes('microphone audio is sent to Groq')")
    disclosure = page.locator("#privacy-note")
    assert disclosure.is_visible()
    assert "microphone audio is sent to Groq" in disclosure.inner_text()
    assert page.evaluate("window.__captureRequests") == 0


def test_practice_navigation_stops_live_visualizer_and_discards_capture(local_app_url: str, browser_page) -> None:
    page = browser_page
    _mock_available_voice_status(page)
    page.add_init_script(_recording_and_deferred_transcription_script("__practiceNavigationSttSignal"))
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    page.locator("#record-button").click()
    page.wait_for_function("() => document.querySelector('#record-status').textContent.startsWith('Recording')")
    assert "is-active" in (page.locator("#recording-visualizer").get_attribute("class") or "")
    page.locator("#career-toggle").click()

    assert page.locator("#career-view").is_visible()
    assert "is-active" not in (page.locator("#recording-visualizer").get_attribute("class") or "")
    assert page.evaluate("window.__practiceNavigationSttSignal === undefined")



def test_career_workspace_cards_and_accessible_question_progress(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator("#career-view").wait_for(state="visible")
    # Career catalog hydration is async; wait for the completed render rather than
    # asserting against the intentional empty/loading state immediately.
    page.wait_for_function("() => document.querySelectorAll('.career-studio-card').length === 3")
    cards = page.locator(".career-studio-card")
    assert cards.count() == 3
    assert page.locator("#career-studio-list").get_by_role("button", name="Choose Project Explanation Studio").count() == 1
    assert "Private local practice" in page.locator(".career-local-note").inner_text()

    page.locator(".career-studio-card").filter(has_text="Project Explanation Studio").get_by_role("button").click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    progress = page.locator("#career-progress-track")
    assert progress.get_attribute("role") == "progressbar"
    assert int(progress.get_attribute("aria-valuemax")) > 0
    assert progress.get_attribute("aria-valuenow") == "0"
    assert page.locator("#career-draft-status").inner_text() == "Nothing saved for this question yet"
    page.locator("#career-answer").fill("An editable first draft")
    assert page.locator("#career-draft-status").inner_text() == "Draft in progress · not saved"



def test_stage8_skip_link_and_primary_navigation_are_accessible(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")

    skip = page.locator(".skip-link")
    skip.focus()
    assert skip.is_visible()
    skip.press("Enter")
    assert page.locator("#main-content").evaluate(
        "(element) => document.activeElement === element"
    )

    destinations = [
        ("home-toggle", "dashboard-view"),
        ("practice-toggle", "home-view"),
        ("learning-toggle", "learning-view"),
        ("career-toggle", "career-view"),
        ("memory-toggle", "memory-view"),
        ("progress-toggle", "progress-view"),
        ("history-toggle", "history-view"),
    ]
    for button_id, view_id in destinations:
        button = page.locator(f"#{button_id}")
        button.click()
        page.locator(f"#{view_id}").wait_for(state="visible")
        assert button.get_attribute("aria-current") == "page"
        assert button.evaluate(
            "(element) => document.activeElement === element"
        ) is False  # focus moves to the newly opened workspace
        if button_id == "memory-toggle":
            assert page.locator("#memory-view").evaluate(
                "(element) => document.activeElement === element"
            )
        else:
            assert page.locator(f"#{view_id}").evaluate(
                "(element) => document.activeElement === element"
            )
        assert page.locator(".nav-button[aria-current='page']").count() == 1
        assert page.locator(".nav-button[aria-expanded]").count() == 0


def test_stage9_release_smoke_all_workspaces_at_supported_widths(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    runtime_errors: list[str] = []
    page.on("pageerror", lambda error: runtime_errors.append(str(error)))
    page.emulate_media(reduced_motion="reduce")
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")

    destinations = [
        ("home-toggle", "dashboard-view"),
        ("practice-toggle", "home-view"),
        ("learning-toggle", "learning-view"),
        ("career-toggle", "career-view"),
        ("memory-toggle", "memory-view"),
        ("progress-toggle", "progress-view"),
        ("history-toggle", "history-view"),
    ]
    for width in (1280, 768, 390):
        page.set_viewport_size({"width": width, "height": 900})
        for button_id, view_id in destinations:
            page.locator(f"#{button_id}").click()
            page.locator(f"#{view_id}").wait_for(state="visible")
            if button_id == "memory-toggle":
                assert page.locator("#memory-view").evaluate(
                    "(element) => document.activeElement === element"
                )
                assert page.locator("#memory-view").is_visible()
                assert not page.locator("#learning-view").is_visible()
            else:
                assert page.locator(f"#{view_id}").evaluate(
                    "(element) => document.activeElement === element"
                )
            assert page.locator(f"#{button_id}").get_attribute("aria-current") == "page"
            assert page.locator(".nav-button[aria-current='page']").count() == 1
        dimensions = page.evaluate(
            "() => ({viewport: innerWidth, document: document.documentElement.scrollWidth})"
        )
        assert dimensions["document"] <= dimensions["viewport"], (
            f"horizontal overflow at {width}px: {dimensions}"
        )

    assert not runtime_errors, f"uncaught browser errors: {runtime_errors}"


def test_profile_destination_and_modal_keyboard_focus_are_integrated(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.wait_for_function(
        "() => document.querySelector('#profile-save-status').textContent === 'Not set up'"
    )

    # Desktop Profile is a dedicated workspace separate from Today.
    page.locator("#profile-nav-toggle").click()
    page.locator("#profile-view").wait_for(state="visible")
    assert not page.locator("#dashboard-view").is_visible()
    assert page.locator("#profile-form").is_visible()
    assert page.locator("#profile-edit-toggle").get_attribute("aria-expanded") == "true"
    assert page.locator("#profile-nav-toggle").get_attribute("aria-current") == "page"
    assert page.locator(".nav-button[aria-current='page']").count() == 1

    # Moving to another workspace clears the Profile destination state.
    page.locator("#learning-toggle").click()
    assert page.locator("#profile-nav-toggle").get_attribute("aria-current") is None

    # Dialog keyboard focus remains inside the active modal and Escape restores focus.
    trigger = page.locator("#help-open-btn")
    trigger.click()
    modal = page.locator("#help-modal")
    modal.wait_for(state="visible")
    first = modal.locator(
        "button:visible, a[href]:visible, input:visible, select:visible, textarea:visible"
    ).first
    first.focus()
    page.keyboard.press("Shift+Tab")
    assert page.evaluate(
        "() => document.activeElement?.closest('#help-modal') !== null"
    )
    page.keyboard.press("Escape")
    assert modal.is_hidden()
    assert trigger.evaluate("(element) => document.activeElement === element")

    # The mobile More sheet routes Profile & Goals through the same handler.
    page.set_viewport_size({"width": 390, "height": 844})
    page.locator("#mobile-more-trigger").click()
    page.locator("#mobile-more-sheet").wait_for(state="visible")
    page.get_by_role("button", name="Profile & Goals").click()
    assert page.locator("#profile-form").is_visible()
    assert page.locator("#profile-nav-toggle").get_attribute("aria-current") == "page"


def test_lesson_focus_mode_hides_global_navigation_and_confirms_exit(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    open_lesson_in_browser(page, "sentence-building")
    page.locator("#learning-runner").wait_for(state="visible")
    page.wait_for_function("() => document.body.classList.contains('lesson-focus-mode')")

    assert not page.locator(".site-header").is_visible()
    assert not page.locator(".app-topbar").is_visible()
    assert not page.locator("#learning-view .learning-welcome").is_visible()
    assert not page.locator("#learning-view .learning-curriculum-section").is_visible()
    skip_rect = page.locator(".skip-link").bounding_box()
    assert skip_rect is not None and skip_rect["y"] + skip_rect["height"] <= 0, skip_rect
    page.set_viewport_size({"width": 390, "height": 844})
    assert not page.locator(".mobile-bottom-nav").is_visible()
    assert page.locator("#learning-runner").is_visible()

    page.locator("#learning-focus-exit").click()
    dialog = page.locator("#lesson-exit-dialog")
    dialog.wait_for(state="visible")
    page.locator("#lesson-exit-keep").click()
    assert dialog.is_hidden()
    assert page.locator("#learning-runner").is_visible()

    page.locator("#learning-focus-exit").click()
    page.locator("#lesson-exit-confirm").click()
    page.wait_for_function("() => !document.body.classList.contains('lesson-focus-mode')")
    assert page.locator("#learning-runner").is_hidden()
    assert page.locator(".mobile-bottom-nav").is_visible()


def test_career_technical_filter_matches_studio_category_not_description(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#career-toggle").click()
    page.locator("#career-view").wait_for(state="visible")
    page.wait_for_function("() => document.querySelectorAll('.career-studio-card').length === 3")

    page.locator('#career-filter-bar button[data-career-filter="technical"]').click()
    visible_titles = page.locator(".career-studio-card:not(.hidden) h3").all_inner_texts()
    assert visible_titles == ["Technical Interview Studio"], f"Unexpected Technical filter matches: {visible_titles}"

    page.locator('#career-filter-bar button[data-career-filter="hr"]').click()
    hr_titles = page.locator(".career-studio-card:not(.hidden) h3").all_inner_texts()
    assert hr_titles == ["HR & Behavioural Interview Studio"], f"Unexpected HR filter matches: {hr_titles}"

    page.locator('#career-filter-bar button[data-career-filter="project"]').click()
    proj_titles = page.locator(".career-studio-card:not(.hidden) h3").all_inner_texts()
    assert proj_titles == ["Project Explanation Studio"], f"Unexpected Project filter matches: {proj_titles}"


def test_practice_textarea_and_record_button_have_light_theme_contrast(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")

    colors = page.evaluate("""() => {
      const ta = getComputedStyle(document.querySelector('#answer-input'));
      const btn = getComputedStyle(document.querySelector('#record-button'));
      return {
        taBg: ta.backgroundColor,
        taColor: ta.color,
        btnBg: btn.backgroundColor,
        btnColor: btn.color,
      };
    }""")
    # Textarea must be warm cream surface (#FFFCF7 = rgb(255, 252, 247)), not legacy dark #121510.
    assert colors["taBg"] == "rgb(255, 252, 247)", colors
    assert colors["taColor"] == "rgb(22, 32, 31)", colors
    # Record button must have pure white label text on deep teal (#0F5C57 = rgb(15, 92, 87)).
    assert colors["btnBg"] == "rgb(15, 92, 87)", colors
    assert colors["btnColor"] == "rgb(255, 255, 255)", colors


def test_career_prompt_and_practice_spoken_prompt_have_high_contrast(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)

    # Verify Career active prompt text is pure white on dark teal card.
    page.locator("#career-toggle").click()
    page.wait_for_function("() => document.querySelectorAll('.career-studio-card').length === 3")
    page.locator(".career-studio-card button").first.click()
    page.locator("#career-start").click()
    page.locator("#career-active").wait_for(state="visible")
    career_colors = page.evaluate("""() => {
      const card = getComputedStyle(document.querySelector('.career-prompt-card'));
      const title = getComputedStyle(document.querySelector('#career-prompt-title'));
      return { bg: card.backgroundColor, titleColor: title.color };
    }""")
    assert career_colors["bg"] == "rgb(23, 62, 57)", career_colors
    assert career_colors["titleColor"] == "rgb(255, 255, 255)", career_colors

    # Verify Practice spoken prompt text and Play button are readable on dark teal card.
    page.locator("#practice-toggle").click()
    page.locator("#start-button").click()
    page.locator("#practice-view").wait_for(state="visible")
    practice_colors = page.evaluate("""() => {
      const hint = getComputedStyle(document.querySelector('.practice-question-card .spoken-prompt-hint'));
      const play = getComputedStyle(document.querySelector('#tts-play-button'));
      return { hintColor: hint.color, playBg: play.backgroundColor, playColor: play.color };
    }""")
    assert practice_colors["hintColor"] == "rgb(220, 238, 233)", practice_colors
    assert practice_colors["playBg"] == "rgb(255, 255, 255)", practice_colors
    assert practice_colors["playColor"] == "rgb(14, 47, 43)", practice_colors


def test_today_start_button_nowrap_and_learn_caps_recommendations(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")
    page.wait_for_function("() => document.querySelector('.dashboard-lesson-action') !== null")
    white_space = page.evaluate("() => getComputedStyle(document.querySelector('.dashboard-lesson-action')).whiteSpace")
    assert white_space == "nowrap", white_space

    page.locator("#learning-toggle").click()
    page.wait_for_function("() => document.querySelector('#learning-status').textContent.includes('skills')")
    # Recommended section shows at most 2 cards by default to keep Learn compact.
    assert page.locator("#learning-recommendations .learning-card").count() <= 2


def test_motion_system_assets_tabs_and_reduced_motion_safety(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    runtime_errors: list[str] = []
    page.on("pageerror", lambda error: runtime_errors.append(str(error)))
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")

    # Living inline SVG owl hydrates cleanly and sound toggle starts OFF.
    assert page.locator(".living-owl").is_visible()
    sound_btn = page.locator("#sound-toggle-btn")
    assert sound_btn.get_attribute("aria-pressed") == "false"
    sound_btn.click()
    assert sound_btn.get_attribute("aria-pressed") == "true"
    sound_btn.click()
    assert sound_btn.get_attribute("aria-pressed") == "false"

    # FLIP sliding thumb initializes on Progress segmented tabs and tracks active tab.
    page.locator("#progress-toggle").click()
    page.locator("#progress-view").wait_for(state="visible")
    page.wait_for_function("() => document.querySelector('#progress-tabs .seg-thumb') !== null")
    before_x = page.evaluate("() => document.querySelector('#progress-tabs .seg-thumb').style.transform")
    page.locator('#progress-tabs button[data-progress-tab="plan"]').click()
    page.wait_for_function(
        "(prev) => document.querySelector('#progress-tabs .seg-thumb').style.transform !== prev",
        arg=before_x,
    )

    # Reduced motion keeps all workspaces overflow-free with zero JS errors.
    page.emulate_media(reduced_motion="reduce")
    page.set_viewport_size({"width": 390, "height": 844})
    page.locator("#home-toggle").click()
    dims = page.evaluate("() => ({w: innerWidth, s: document.documentElement.scrollWidth})")
    assert dims["s"] <= dims["w"], dims
    assert not runtime_errors, runtime_errors


def test_packs_abcd_preferences_shortcuts_heatmap_and_career_studio_in_browser(
    local_app_url: str, browser_page
) -> None:
    page = browser_page
    runtime_errors: list[str] = []
    page.on("pageerror", lambda error: runtime_errors.append(str(error)))
    page.goto(local_app_url)
    page.locator("#dashboard-view").wait_for(state="visible")

    page.keyboard.press("?")
    page.locator("#shortcuts-modal").wait_for(state="visible")
    page.keyboard.press("Escape")
    assert page.locator("#shortcuts-modal").is_hidden()

    page.locator("#profile-nav-toggle").click()
    page.locator("#profile-view").wait_for(state="visible")
    page.locator("#pref-theme").select_option("dark")
    page.locator("#pref-text-size").select_option("large")
    page.locator("#preferences-save-btn").click()
    page.wait_for_function("() => document.documentElement.dataset.theme === 'dark'")
    assert page.evaluate("() => document.documentElement.dataset.textSize") == "large"

    page.locator("#progress-toggle").click()
    page.locator("#progress-view").wait_for(state="visible")
    page.wait_for_function("() => document.querySelectorAll('#progress-heatmap .heatmap-cell').length === 84")
    assert page.locator("#progress-heatmap .heatmap-cell").count() == 84

    page.locator("#career-toggle").click()
    page.locator('#career-stage-tabs button[data-career-nav="projects"]').click()
    page.locator("#career-projects-stage").wait_for(state="visible")
    page.locator("#proj-title").fill("Local Study Companion")
    page.locator("#proj-problem").fill("Students needed offline interview rehearsal.")
    page.locator("#proj-save-btn").click()
    page.wait_for_function("() => document.querySelector('#project-studio-list').textContent.includes('Local Study Companion')")

    page.locator('#career-stage-tabs button[data-career-nav="warmup"]').click()
    page.locator("#mock-active-panel").wait_for(state="visible")
    page.locator("#mock-answer-input").fill("I am a computer science student and I built a FastAPI tool with automated tests.")
    page.locator("#mock-finish-early-btn").click()
    page.locator("#mock-debrief-panel").wait_for(state="visible")
    assert "does not score ability" in page.locator("#mock-debrief-disclaimer").inner_text()
    assert not runtime_errors, runtime_errors
