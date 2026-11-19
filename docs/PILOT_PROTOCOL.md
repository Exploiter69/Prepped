# Prepped — First Student Usability Pilot Protocol

**Status:** Future validation activity; no pilot results have been collected. This is **not an engineering blocker**.<br>
**Version:** 1.1 · **Updated:** 2026-11-04

## Purpose

Find out whether students can complete the local project-interview practice loop, understand its feedback, and identify a useful next action. This is a usability and formative-feedback check, not a study proving improved placement outcomes or speech accuracy.

## Relationship to engineering

Product development and user validation are separate tracks:

- Engineering continues on the local voice slice, failure handling, tests, privacy, and maintainability without waiting for this pilot.
- This protocol is used when participants and an appropriate setting are available.
- No pilot result is claimed until it is actually collected and written up with method, sample size, and limitations.
- A pilot is not required to “unlock” voice or other engineering work. It informs future priorities; it does not replace technical acceptance.

## Optional voice addendum

If the participant is comfortable using a microphone, add these steps after the text flow:

1. Press **Play question aloud**, then **Stop**, then **Replay**.
2. Press **Start recording**, allow microphone permission, speak one short answer, and press **Stop recording**.
3. Correct one transcription error before saving.
4. Deny microphone permission in a second browser/profile and recover using text.

Record only whether the flow was understandable and whether the transcript was editable/useful. Do **not** retain raw audio, recordings, or full personal answers. Speech-recognition accuracy is not established by this usability check.

## Participants and scope

- Aim for 10–20 student volunteers if available; record the actual sample size.
- Participation is voluntary. Do not recruit anyone under pressure or imply academic/placement benefit.
- Do not ask for names, roll numbers, phone numbers, resumes, confidential project details, or recordings.
- Use a fictional project or a non-sensitive project example.
- Do not record screens, audio, or full answers by default. Record anonymous observations only.

## Participant introduction (read aloud)

“Prepped is an early practice prototype. Its feedback uses simple text rules and can be wrong. It is not a placement test, hiring decision, or prediction of your performance. Taking part is voluntary. Please use a fictional or non-sensitive example. I will note usability observations without your name; you can stop at any time.”

Proceed only if the participant agrees to try the prototype. If they do not agree, thank them and stop.

## Task script

1. Start a new session and explain a project using the five prompts.
2. Review the feedback and identify one item that quotes or refers to something actually said.
3. Explain in their own words what one feedback item is asking them to improve.
4. Retry the scenario with any changes they choose.
5. Compare the attempts and explain what changed.
6. Find session history and delete one session.

Do not coach during the first attempt. If help is needed, provide it and mark the task as completed with help.

## Record for each anonymous participant

Use IDs such as P01, P02; do not record names or contact details.

- Date (or session batch), participant code, and whether consent to anonymous observation was given.
- Task outcomes: completed independently / completed with help / not completed.
- Approximate completion time, if practical.
- Where they hesitated or misunderstood the interface.
- Feedback grounding: did the quoted evidence match their own answer? yes / partly / no / unclear.
- Next-action comprehension: could they explain what to try next? yes / partly / no.
- Attempt comparison: could they identify a change? yes / partly / no.
- Would they voluntarily practise again? yes / unsure / no.
- Bugs or unexpected behaviour; do not copy full personal answers into the notes.

## Per-session observation sheet

| Measure | Result |
|---|---|
| Participant code | |
| Completed first attempt | Independent / Help / No |
| Understood feedback evidence | Yes / Partly / No |
| Understood a next action | Yes / Partly / No |
| Completed retry | Independent / Help / No |
| Understood attempt comparison | Yes / Partly / No |
| Found and deleted history item | Yes / Partly / No |
| Would practise again | Yes / Unsure / No |
| Main confusion or bug | |
| One suggested improvement | |

## Summary report template

- **Date and setting:**
- **Number invited / participated / completed:**
- **Device/browser and app version:**
- **Method and deviations from this protocol:**
- **Task completion counts:** report numerator and denominator for every count.
- **Feedback grounding:** yes / partly / no / unclear counts.
- **Next-action comprehension:** yes / partly / no counts.
- **Attempt comparison and deletion findings:**
- **Top three usability issues, with anonymous examples:**
- **Unexpected failures:**
- **Changes recommended and why:**
- **Limitations:** convenience sample, small sample size, self-report/observer effects, prototype status, and no evidence of placement or learning improvement.
- **Decision:** iterate the current voice/text slice / repeat pilot / defer voice changes pending more engineering evidence. Explain the evidence behind the choice.

## Stop and privacy rules

- Stop if a participant becomes uncomfortable or wants to withdraw.
- Do not save raw audio or video.
- Avoid storing actual participant answers in a shared repository.
- Keep only anonymous, minimal observation notes; delete them when no longer needed.
- Never report invented results or generalize beyond the participants and tasks observed.
- A successful usability pilot does not establish learning gains or placement-readiness improvement.
