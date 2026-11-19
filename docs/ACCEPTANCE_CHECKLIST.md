# Prepped — Foundation Acceptance Checklist

**Purpose:** Record repeatable acceptance evidence for the learner profile, existing practice room, and record/stop voice slice before beginning the Learning Engine.
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
python -m pytest -q
```

Expected:
- Dependency installation completes without a paid service or API key.
- Python compilation and both JavaScript syntax checks exit successfully.
- The complete test suite passes. The optional Playwright browser tests exercise profile open/save/edit/cancel/reload and the text-only practice journey in Chromium. The profile unit tests also assert the served page's accessible toggle/form contract. CI installs the optional browser-test extra and Chromium; the application itself does not require Playwright. Record the exact pass/skip count and any warnings.
- A skipped real-model integration test is recorded as skipped, not passed.

Latest recorded Chromium CI acceptance: [run 44534499386](https://github.com/Exploiter69/Prepped/actions/runs/44534499386) — 41 passed, 2 skipped, 1 warning. The skips require `espeak-ng`, unavailable on the hosted runner. CI runs on pushes to `feature/**` and pull requests targeting `feature/learner-profile` or `main`. A green CI run is evidence for the checked commit only.

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
- [ ] Confirm prerequisite lessons are disabled until the required lesson is completed; retry remains available after completion.

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
