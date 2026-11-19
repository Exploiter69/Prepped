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


def complete_lesson_in_browser(page, lesson_id: str, answers: list[str | list[str]]) -> None:
    page.locator(f'button[data-lesson-id="{lesson_id}"]').click()
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

    page.locator("#question-feedback button").filter(has_text="Save a learning note").first.click()
    page.locator("#learning-view").wait_for(state="visible")
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
    assert "Lessons completed" in page.locator("#learning-progress").inner_text()
    next_lesson = page.locator("#learning-feedback button").filter(has_text="Next lesson: Shape a sentence for clarity")
    assert next_lesson.is_visible()
    next_lesson.click()
    page.wait_for_function(
        "() => document.querySelector('#learning-runner-title').textContent.includes('Shape a sentence for clarity')"
    )


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
    page.get_by_role("button", name="Back to lesson list").click()

    page.locator('button[data-lesson-id="listening-for-details"]').click()
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
    lesson = page.locator('button[data-lesson-id="speaking-opinions"]')
    assert lesson.is_enabled()
    lesson.click()
    page.locator("#learning-runner").wait_for(state="visible")
    assert "Express an opinion" in page.locator("#learning-runner-title").inner_text()


def test_english_track_exposes_complete_phase_c_units(local_app_url: str, browser_page) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#learning-toggle").click()
    page.wait_for_function(
        "() => document.querySelector('#learning-status').textContent.includes('skills')"
    )
    track = page.locator(".learning-track").filter(has_text="English foundations")
    assert track.locator(".learning-unit").count() == 6
    assert track.locator(".learning-unit-outcomes li").count() >= 12
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
    page.locator('button[data-lesson-id="pronunciation-self-review"]').click()
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
    page.locator('button[data-lesson-id="listening-conversations"]').click()
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
    page.locator("#learning-toggle").click()
    page.locator("#memory-front").fill("in the long run")
    page.locator("#memory-back").fill("Over a long period of time.")
    page.locator("#memory-form button[type='submit']").click()
    page.wait_for_function(
        "() => document.querySelector('#memory-items').textContent.includes('in the long run')"
    )
    assert "Active cards" in page.locator("#memory-stats").inner_text()
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
    page.locator("#learning-feedback button").filter(has_text="Save a learning note").first.click()
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
    page.locator("#career-history-list button").filter(has_text="Open").nth(1).click()
    page.locator("#career-review").wait_for(state="visible")
    page.locator(".career-review-card button").first.click()
    page.locator("#learning-view").wait_for(state="visible")
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
    assert "which experience or project" in page.locator("#career-prompt-title").inner_text().lower()


def test_progress_goals_and_backup_restore_in_browser(local_app_url: str, browser_page, tmp_path: Path) -> None:
    page = browser_page
    page.goto(local_app_url)
    page.locator("#progress-toggle").click()
    page.locator("#progress-status").wait_for()
    page.wait_for_function("() => document.querySelector('#progress-status').textContent.startsWith('Updated')")
    assert page.locator("#progress-summary .progress-stat").count() == 6

    page.locator("#goal-title").fill("Complete two lessons")
    page.locator("#goal-type").select_option("lessons_completed")
    page.locator("#goal-target").fill("2")
    page.locator("#goal-form button[type='submit']").click()
    assert "Complete two lessons" in page.locator("#progress-goals").inner_text()
    assert "0 / 2" in page.locator("#progress-goals").inner_text()

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
    assert "Complete two lessons" in page.locator("#progress-goals").inner_text()


def test_progress_navigation_and_security_headers_are_accessible(local_app_url: str, browser_page) -> None:
    page = browser_page
    response = page.goto(local_app_url)
    assert response is not None
    assert response.headers.get("content-security-policy")
    assert response.headers.get("x-content-type-options") == "nosniff"
    toggle = page.locator("#progress-toggle")
    assert toggle.get_attribute("aria-controls") == "progress-view"
    toggle.click()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert page.locator("#progress-view").is_visible()
    page.locator("#learning-toggle").click()
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.locator("#learning-view").is_visible()
