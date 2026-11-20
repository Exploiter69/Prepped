# Prepped — A–F Learner Acceptance Checklist

**Purpose:** Record repeatable learner acceptance evidence for Phases A–F. Phase G release hardening and final sign-off are tracked separately in [PHASE_G_ACCEPTANCE.md](PHASE_G_ACCEPTANCE.md). This checklist includes the foundation, Learning Engine, English curriculum, memory, Career studios, Progress, portability, voice, privacy, and device acceptance.
**Environment:** Local FastAPI app, SQLite database, current `feature/learner-profile` branch.
**Rule:** Mark a check only after performing it. Automated tests do not replace browser acceptance.

## 1. Automated and clean-checkout checks

Run from a clean checkout or a clean worktree after syncing the branch:

```bash
python -m pip install -e ".[dev,browser-test]"
python -m playwright install chromium
python -m compileall -q prepped
node --check static/app.js
node --check static/voice.js
node --check static/learning.js
node --check static/memory.js
node --check static/career.js
node --check static/progress.js
python -m pytest -q
```

Expected:
- Dependency installation completes without a paid service or API key.
- Python compilation and all six browser JavaScript syntax checks exit successfully.
- The complete test suite passes. The Playwright browser tests exercise profile open/save/edit/cancel/reload, the text-only practice journey, and the Phase B–F learner flows in Chromium. The profile unit tests also assert the served page's accessible toggle/form contract. CI installs the optional browser-test extra and Chromium; the application itself does not require Playwright. Record the exact pass/skip count and any warnings.
- A skipped real-model integration test is recorded as skipped, not passed.

Latest full-suite Chromium CI acceptance: [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning. The skips require `espeak-ng`, unavailable on the hosted runner. CI runs on pushes to `feature/**` and pull requests targeting `feature/learner-profile` or `main`. A green CI run is evidence for the checked commit only.

## 2. Learner profile — browser acceptance

Start the app with the normal local command and open `http://127.0.0.1:8000`.

- [ ] On a fresh test database, the profile summary explains that setup is optional.
- [ ] **Set up profile** opens the form; the button label and `aria-expanded` state change to the open state.
- [ ] Cancel closes the form without creating a profile.
- [ ] The learner can save a profile with optional fields left blank.
- [ ] The saved summary displays the selected goal, year/branch when present, and focus areas.
- [ ] Edit opens the form populated with the saved values.
- [ ] Cancel during edit restores the saved values and closes the form.
- [ ] Saving edits updates the summary and survives a page reload and app restart.
- [ ] Invalid values show a useful error and do not erase the previous saved profile.
- [ ] Skipping profile setup does not block starting the existing practice room.
- [ ] Keyboard-only use can reach the toggle, form controls, save, and cancel; focus remains visible.

API spot checks:

```bash
curl -i http://127.0.0.1:8000/api/profile
```

A fresh database should return HTTP 200 with `configured: false` and `profile: null`. After saving in the UI, the endpoint should return the stored profile. Do not use real personal data in disposable acceptance databases.

## 3. Existing text practice regression

- [ ] Start the project-explanation practice without configuring a profile.
- [ ] Confirm all five existing prompts appear in order.
- [ ] Submit a typed answer, then use Skip on a later prompt.
- [ ] Confirm answers are saved and the session completes only after the final prompt.
- [ ] Confirm feedback quotes the submitted answer and describes its heuristic limitations; no overall score appears.
- [ ] Retry the completed session and confirm it uses the same scenario/rubric snapshot.
- [ ] Confirm history shows the session and its attempt; review and delete work.
- [ ] Confirm a page reload or app restart does not remove saved history.

## 4. Voice acceptance — optional local tools

Voice availability depends on the local machine. Text practice must remain usable when microphone access, ffmpeg, STT, or TTS is unavailable.

Check the advertised engines:

```bash
curl -sS http://127.0.0.1:8000/api/voice/status
```

If a local Vosk model and ffmpeg are installed:

- [ ] The UI clearly identifies local Vosk before recording.
- [ ] Grant microphone permission and record a short answer.
- [ ] Stop recording; confirm a transcript is inserted into the existing editable answer field.
- [ ] Correct a transcription error and submit the edited text.
- [ ] Confirm the corrected text, not an immutable raw transcript, is saved in the session.
- [ ] Play a prompt aloud, stop playback, and replay it if a local TTS engine is available.
- [ ] Deny microphone permission and confirm text entry still works.
- [ ] Confirm recording stops at the configured limit and when the active prompt/session changes.
- [ ] Confirm raw audio is not retained by Prepped.

If Groq is explicitly configured for a separate test:

- [ ] Confirm the UI discloses that audio leaves the device before recording.
- [ ] Use only a non-sensitive test recording.
- [ ] Confirm transcript editing and normal local answer submission still work.
- [ ] Do not commit the API key, logs containing it, or test recordings.

Record the provider used, local tool/model availability, browser, operating system, and any failure. Do not describe a mocked test as a live provider test or a successful synthetic sample as proof of Indian-English accuracy.

## 5. Data safety and regression

- [ ] Run acceptance against a disposable test database where possible.
- [ ] Confirm the additive profile migration leaves existing session and answer rows intact.
- [ ] Confirm profile save/edit does not modify practice history.
- [ ] Confirm no raw audio files are created by the application.
- [ ] Confirm local database/model files and secrets remain ignored and are not committed.



## Phase C — English and communication studio manual acceptance

These checks require a real browser on the target laptop. Mark each item only after performing it; automated tests do not prove microphone, speaker, or learning-content usability.

### Curriculum and profile recommendations

- [ ] Open Learning and confirm the English foundations path shows all 11 lessons across sentence, grammar, vocabulary, listening, speaking, and pronunciation units.
- [ ] Confirm every unit has clear outcomes and every lesson displays its outcomes, estimated time, summary, exercise count, prerequisite guidance, and a working start/retry action.
- [ ] Set the profile goal to English fluency and focus areas to grammar, vocabulary, speaking fluency, pronunciation, confidence, and professional communication; save and reopen Learning.
- [ ] Confirm recommendation explanations point to the relevant lessons and that the route does not claim to infer ability or proficiency.
- [ ] Confirm the project-communication and placement-communication tracks and the original practice room remain available.

### Sentence and grammar practice

- [ ] Complete sentence construction and sentence shaping: build, expand, combine, shorten, and clarify while preserving intended meaning.
- [ ] Complete grammar exercises for past/future tense, articles, and common prepositions; confirm authored explanations appear for selected answers.
- [ ] Complete question formation for present-simple and past-simple questions and write a polite clarification question.
- [ ] Confirm open responses are retained for self-review and are not automatically graded.

### Vocabulary and useful phrases

- [ ] Complete contextual word-choice and collocation exercises.
- [ ] Review the meaning of a phrase in its scenario context.
- [ ] Write a learner-authored example using one of the taught phrases; confirm the original response is visible in lesson review.
- [ ] Confirm no vocabulary card is silently created or stored as permanent learner memory; learner-controlled saving belongs to Phase D.

### Speaking fluency and confidence

- [ ] Complete structured description, process explanation, technical/feature explanation, and retelling prompts.
- [ ] Complete an opinion prompt and its follow-up; confirm the activity accepts a typed response without microphone access.
- [ ] If recording is available, confirm the disclosure appears before microphone permission. In Groq mode, confirm it says the recording is sent to Groq.
- [ ] Confirm the transcript can be reviewed and edited before submission, and text entry remains usable if recording/transcription fails.
- [ ] Confirm feedback does not assign a fluency, confidence, personality, or emotion score.

### Listening and pronunciation

- [ ] Play, stop, and replay each listening message; reveal and hide its transcript alternative.
- [ ] Complete both listening-for-details and short-conversation comprehension activities.
- [ ] Open each pronunciation model phrase, play/replay it, and reveal the phrase text alternative.
- [ ] Repeat each phrase at a comfortable pace and submit an optional self-review note or editable spoken transcript.
- [ ] Confirm pronunciation feedback explicitly states that no pronunciation, accent, phoneme, or fluency score is measured.
- [ ] Confirm listening and pronunciation remain understandable when TTS is unavailable by using their text alternatives.

### Accessibility, privacy, and responsive behavior

- [ ] Complete a lesson using keyboard-only navigation and confirm visible focus and meaningful control labels.
- [ ] Check the Learning workspace at laptop width and a narrow mobile viewport; confirm no card, prompt, transcript, or control overflows.
- [ ] Confirm audio playback stops when leaving a lesson or switching workspaces.
- [ ] Confirm no raw audio is saved by Prepped. Treat any Groq transcription as remote processing, not local-only processing.
- [ ] Confirm the existing practice room, history, profile, and saved learning attempts remain intact after reload.

## 6. Acceptance record

Copy this record into the release notes or issue after the checks are actually performed:

| Field | Record |
|---|---|
| Commit SHA | |
| Date | |
| OS / browser | |
| Automated tests | |
| CI run URL / result | |
| Profile flow | Pass / Fail / Not run |
| Text practice | Pass / Fail / Not run |
| Voice provider / model | |
| Voice flow | Pass / Fail / Not available / Not run |
| Data-preservation check | Pass / Fail / Not run |
| Known issues | |

**Exit gate:** Automated checks and CI pass, profile and text practice browser journeys pass, and voice results/limitations are recorded. If voice hardware or models are unavailable, record that limitation; do not block text-mode development or claim voice acceptance.

## Phase B — Learning Engine manual acceptance

These checks complement API and Chromium automation. Record the date, browser, device, and any failure before marking a box complete.

### Curriculum and profile route

- [ ] Open **Learning** from the header; confirm the workspace loads without hiding or breaking the existing practice room.
- [ ] Confirm the skill map distinguishes active and planned skills and shows outcomes/progress without a proficiency score.
- [ ] Confirm tracks display their foundation stage, units, lessons, estimated effort, and prerequisites.
- [ ] Change the learner profile goal to English fluency, save, reopen Learning, and confirm the recommended route changes to English foundations.
- [ ] Select grammar, vocabulary, and speaking-fluency focus areas; confirm the route explains the matching lessons. Confirm unsupported areas are disclosed as not yet covered.
- [ ] Confirm lessons remain openable even when suggested prerequisites are incomplete; prerequisite guidance recommends an order without locking lessons.

### Low-stakes starting point check

- [ ] Start the optional Starting point check and complete sentence, ordering, listening, and project-response tasks.
- [ ] Confirm it records the responses without displaying a total score, proficiency level, CEFR label, or placement prediction.
- [ ] Repeat the check and confirm both attempts remain available in saved diagnostic history for later comparison.
- [ ] Confirm diagnostic completions are counted separately and do not inflate normal lesson or skill completion.

### Lesson runner and persistence

- [ ] Complete a choice exercise and confirm the selected answer, correct answer, and authored explanation are shown.
- [ ] Complete an ordering exercise and confirm missing/duplicate items are rejected and the suggested order is shown.
- [ ] Complete a short response; confirm the original response, self-review guidance, and illustrative example are shown without an automatic grade.
- [ ] Reload during an unfinished lesson and resume at the exact next exercise.
- [ ] Complete a lesson and follow the next-lesson action; confirm the next prerequisite is satisfied.
- [ ] Reopen Learning and confirm progress counts and completed lesson state persist.

### Listening and spoken response

- [ ] Start a listening lesson and play the spoken message; stop playback and replay it.
- [ ] Reveal and hide the text alternative; confirm the listening task remains usable if local TTS is unavailable.
- [ ] If speech-to-text is available, confirm the recording disclosure is visible before microphone access. In Groq mode, confirm it explicitly says audio is sent to Groq.
- [ ] Record a short response, stop, review/edit the transcript, and submit it. Confirm text input remains available if microphone or transcription fails.
- [ ] Confirm no raw audio file is created or retained by Prepped. Do not treat a status endpoint alone as proof of transcription quality.

### Accessibility and responsive behavior

- [ ] Complete the Learning flow using keyboard navigation only; confirm visible focus and meaningful labels.
- [ ] Check the workspace at laptop width and a narrow mobile viewport; confirm cards, controls, and feedback do not overflow.
- [ ] Confirm status/error messages are understandable and the learner can return to the practice room at any point.


## Phase D — Personal learning memory and spaced revision

Run these checks on a disposable database first. Keep the normal local database intact.

### Manual capture and item management

- [ ] Open Learning and find the Personal learning memory section.
- [ ] Create one word, phrase, correction, concept, and example manually; confirm each appears in the local library.
- [ ] From a completed lesson review, choose **Save a learning note**. Confirm it only prefills the editor and does not save until submitted.
- [ ] Confirm lesson-derived and project-practice items retain their source title, attempt identifier, and source excerpt.
- [ ] Edit an item's front and back; confirm its source metadata and review history remain intact.
- [ ] Attempt a duplicate with different case and whitespace; confirm the existing item is identified and not overwritten.
- [ ] Suspend an item; confirm it disappears from the due queue. Resume it and confirm its schedule is preserved.
- [ ] Delete an item; confirm it and its review history are permanently removed after confirmation.

### Review and scheduling

- [ ] Confirm a newly saved active item is due immediately.
- [ ] Reveal a card's answer before rating it.
- [ ] Test Again, Hard, Good, and Easy on separate disposable cards and confirm the next due date and interval are visible/consistent with the documented schedule.
- [ ] Confirm Again increments lapses and resets the repetition step.
- [ ] Confirm a successful review removes the card from the due queue until its next due date.
- [ ] Confirm review history and schedule survive browser reload and application restart.
- [ ] Confirm suspended cards cannot be reviewed until resumed.
- [ ] Confirm the UI and documentation call this a simple local scheduler, not FSRS.

### Automated and data-safety checks

- [ ] Run `python -m compileall -q prepped`.
- [ ] Run `node --check static/app.js`, `node --check static/voice.js`, `node --check static/learning.js`, and `node --check static/memory.js
node --check static/career.js`.
- [ ] Run `python -m pytest -q` and record exact pass/skip counts.
- [x] Confirm GitHub Actions passes for the exact implementation commit: [run 44561847713](https://github.com/Exploiter69/Prepped/actions/runs/44561847713) — 79 passed, 2 skipped (both require `espeak-ng`).
- [ ] Confirm legacy sessions, answers, learner profile, learning attempts, and learning events remain unchanged by the memory migration.
- [ ] Confirm memory items and review history persist in SQLite and no external service or raw audio file is introduced.
- [ ] Check keyboard-only operation, visible focus, screen-reader labels/status, and narrow-screen layout.


## Phase E — Career & Interview Studios manual acceptance

Use a disposable database. Automated Chromium coverage does not replace checking the real microphone, speakers, browser permissions, or target-device layout.

### Studio discovery and setup

- [ ] Open **Career** from the header; confirm the original practice room and Learning workspace remain reachable.
- [ ] Confirm all three studios appear with a clear description, duration, and skill focus.
- [ ] Select each studio and start a guided, standard, and challenging session.
- [ ] Confirm the selected mode changes the authored follow-up wording; the main question remains readable and relevant.

### Project explanation

- [ ] Complete the four main questions and their follow-ups using truthful details from a disposable/sample project.
- [ ] Explain the problem/user, personal contribution, one technical decision, and testing evidence/limitations.
- [ ] Confirm each main question is followed by its own follow-up before the next main question.

### HR and behavioural interview

- [ ] Complete introduction, teamwork, challenge/setback, and motivation questions.
- [ ] Confirm follow-ups ask for specific context, actions, outcomes, or reflection rather than repeating the main prompt.
- [ ] Confirm the UI does not encourage inventing experience; typed answers remain available.

### Technical interview

- [ ] Complete the array/linked-list, HTTP/API, database-index, and process/thread questions.
- [ ] Confirm the authored follow-ups ask for examples, trade-offs, or debugging reasoning.
- [ ] Confirm feedback does not claim to validate technical correctness.

### Voice, persistence, and review

- [ ] Complete an interview entirely by typing with no microphone permission; confirm every follow-up and review works.
- [ ] If local STT is available, record/stop an answer, edit the transcript, and submit the corrected text.
- [ ] If Groq Whisper is configured, confirm the remote-audio disclosure appears before microphone permission is requested.
- [ ] Play a prompt using local TTS; confirm text remains available if TTS is unavailable.
- [ ] Leave an interview in progress, return to it from recent history, and confirm the exact next prompt is restored.
- [ ] Complete an interview, inspect every original answer and review note, retry it, and confirm the new attempt is linked in history.
- [ ] Delete a disposable interview and confirm it and its turns disappear; verify existing practice and learning history remain.
- [ ] Choose **Save answer to learning memory**; confirm the memory editor is prefilled with source context and nothing is saved until submitted. Discard one suggestion and confirm no item was created.
- [ ] Reload and restart the app; confirm completed interview history and unfinished sessions persist.

### Honest feedback, accessibility, and responsive layout

- [ ] Confirm there is no overall interview score, recruiter rating, technical correctness verdict, or placement prediction.
- [ ] Confirm each heuristic signal shows its limitation and does not label a learner's ability.
- [ ] Complete the flow with keyboard navigation and visible focus.
- [ ] Check laptop and narrow-screen widths; confirm studio cards, transcript field, review notes, and history controls do not overflow.
- [ ] Confirm no raw audio files are created by Prepped and text fallback works when voice is unavailable.


### Phase E automated evidence

- [x] Current full-suite GitHub Actions covers Phase E: [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning.
- [ ] Complete the manual target-laptop checks above. CI does not prove microphone permission, live transcription quality, local TTS availability, or device-specific responsive behaviour.


---

## Phase F — Progress, portability, and hardening foundations

### Progress evidence and learner goals

- [ ] Open **Progress**; confirm counts match saved lessons, project sessions, career interviews, and memory reviews.
- [ ] Complete a normal lesson; confirm only the linked skill evidence changes. Complete the baseline diagnostic; confirm it is not counted as a completed curriculum lesson.
- [ ] Confirm skill coverage shows completed lesson evidence and explicitly does not present a proficiency rating.
- [ ] Confirm the seven-day activity view uses saved completion/review timestamps and has a useful empty state on a new database.
- [ ] Confirm recommendations explain why they are shown: unfinished lesson, project-practice session, or interview; due memory notes; profile-selected next lesson; or active learner goal.
- [ ] Create one goal for each supported counter: lessons, project practice sessions, interviews, and memory reviews.
- [ ] Confirm each goal counts only activity after its creation; confirm target count and remaining count update after the corresponding activity.
- [ ] Edit a goal; archive it; show archived goals; restore it; permanently delete it. Confirm deleting a goal does not delete any activity.
- [ ] Reload and restart the application; confirm goals and progress remain correct.

### Export, backup, restore, and recovery

- [ ] Use **Download local backup** and confirm a JSON file downloads without uploading data to an external service.
- [ ] Confirm the backup includes profile, sessions and answers, lesson attempts and events, memory items and review history, career sessions and turns, learner goals, and dismissed recommendation preferences.
- [ ] Confirm the backup does not contain environment variables, API keys, voice model files, or source code.
- [ ] Make a second disposable database and restore the backup there; confirm every table's record counts and representative records match.
- [ ] Restore a valid backup over disposable data only after reading the full-replacement confirmation; confirm all previous target data is replaced, not merged.
- [ ] Try an invalid JSON file, wrong format/version, missing table, unexpected column, oversized file, and broken foreign-key reference. Confirm each restore is rejected and the current database remains unchanged.
- [ ] Confirm a backup from an unsupported future schema is rejected without changing the active database.
- [ ] Keep backup files private; they are unencrypted and contain personal answers/notes.
- [ ] Confirm the readiness endpoint returns ready after a clean install and reports failure when tested against a disposable invalid database/curriculum.

### Security, privacy, and supported environment

- [ ] Start Uvicorn bound to 127.0.0.1; confirm localhost and 127.0.0.1 work and non-local Host values are rejected.
- [ ] Confirm same-origin UI actions work and a mismatched Origin on a state-changing request is rejected.
- [ ] Inspect response headers for CSP, frame denial, MIME sniffing protection, restrictive referrer/permissions policies, and API Cache-Control: no-store.
- [ ] Confirm the microphone works only when requested by the learner and the text-only path remains usable when voice is unavailable.
- [ ] Confirm Groq credentials remain server-side and are not included in exported data; no raw audio is persisted.
- [ ] Confirm the default database, .env, backups, and local voice models remain ignored by Git.
- [ ] Complete a fresh clone/install using [INSTALL.md](INSTALL.md) on the target Omarchy laptop and record Python/browser versions and any deviations.
- [ ] Run the dependency audit and review any advisories; do not describe a CI audit as a third-party penetration test.
- [ ] Complete keyboard-only navigation, visible focus, label/status announcements, screen-reader review, contrast, and narrow-screen checks across Home, Learning, Career, Progress, and History.

### Honest reporting and validation

- [ ] Confirm no total proficiency score, placement prediction, learning-gain claim, technical correctness verdict, or validated speaking score appears.
- [ ] Confirm the progress dashboard calls its measures saved activity and lesson evidence, not ability.
- [ ] Dismiss a suggested next step, reload Progress, confirm it stays dismissed, then restore it from the dismissed-suggestions list.
- [ ] Do not report a student pilot until it has actually been run with consent. Record sample size, method, failures, and limitations; never invent results.

### Phase F automated evidence

- [x] GitHub Actions passes on current Phase A–F implementation commit: [run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning; pip-audit, Python compilation, all JavaScript syntax checks, API tests, and Chromium browser acceptance passed.
- [ ] API tests cover all progress counters/goals, baseline exclusion, recommendation reasons, complete backup table coverage including dismissed recommendation preferences, round-trip restore, invalid backup rollback, size limits, readiness, Host/Origin checks, and security headers.
- [x] Browser tests cover Progress navigation, immediate dismissed-suggestion expansion, goal create/edit/archive/restore, backup download/restore, and cross-workspace navigation (run 44655380427).
- [ ] Complete the manual target-laptop checks above. CI does not prove fresh-install operation on the user's device, microphone permission, speech recognition quality, TTS output, screen-reader behaviour, or device-specific responsive layout.


## Pre-Phase-G sign-off record

**Automated evidence (2026-11-20):** [GitHub Actions run 44655380427](https://github.com/Exploiter69/Prepped/actions/runs/44655380427) — 100 passed, 2 skipped, 1 warning. The two skips require `espeak-ng`, unavailable on the hosted runner. Dependency audit, Python compilation, all JavaScript syntax checks, API tests, and Chromium browser acceptance passed.

**Manual target-laptop evidence:** not yet recorded. Leave the relevant boxes unchecked until each check is actually performed on the target Omarchy laptop. Do not treat CI as microphone, audio-device, screen-reader, contrast, or responsive acceptance.

**Phase G status:** engineering in progress. Target-laptop A–F manual acceptance and clean-install/recovery rehearsal remain mandatory for release sign-off, but do not block code-level Phase G hardening. Track the final gate in [PHASE_G_ACCEPTANCE.md](PHASE_G_ACCEPTANCE.md).
