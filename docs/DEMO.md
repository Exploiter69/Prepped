# Prepped — local demonstration guide

This is a repeatable demonstration of the existing product, not a claim that speech accuracy, learning outcomes, or placement outcomes have been validated.

## Before the demonstration

Use a fresh disposable source checkout if you do not want demo activity saved in your normal local database. The default database is stored under that checkout's data/ directory.

    bash scripts/prepped.sh setup
    bash scripts/prepped.sh start

Open http://127.0.0.1:8000 in a local browser. In another terminal:

    bash scripts/prepped.sh check

The health and readiness checks should report success. Voice status may report unavailable engines; that does not block the text demonstration.

## Offline text-mode walkthrough

After installation and dependency setup, the core demonstration does not require a network connection, API key, speech model, or paid service.

1. **Learner profile:** open the profile form, set a practice goal and focus area, save, reload, and show that the selected route is explained. Profile setup is optional.
2. **Project Practice:** start the project-explanation scenario. Answer the first prompt with a short, truthful description of a project; use text input for the remaining prompts if desired.
3. **Formative review:** complete the scenario and inspect the answer-linked notes. Explain that the heuristic can miss valid answers and is not a score or correctness assessment.
4. **Career Studio:** open Project Explanation Studio, choose a difficulty, answer the authored main and follow-up questions, and inspect the response-specific next action. Do not describe it as an expert interviewer or technical grader.
5. **Learning:** open an English foundations lesson, complete the closed exercises, and use text responses for open reflection. Show the outcome and text alternative where available.
6. **Memory:** explicitly save one useful phrase or correction, edit it, and review it. Nothing is captured from a suggestion until the learner submits it.
7. **Progress:** show evidence categories, due review, a daily/weekly plan, and the reasons behind recommendations. Explain that activity counts are not proficiency or learning-gain scores.
8. **Backup:** use Progress → Download local backup. Treat the resulting JSON as sensitive, unencrypted personal data. Do not upload or share it.

## Optional voice demonstration

Voice is optional. First run the voice-setup command shown below and review the separate model/package licence terms. Confirm /api/voice/status before demonstrating. Use only non-confidential practice speech.

    bash scripts/prepped.sh voice-setup

If Groq is configured, the UI must disclose that audio is sent to Groq before microphone capture. Do not enable a paid plan for the demo. If the provider is not configured, demonstrate text mode or an installed local Vosk/Piper/espeak-ng path; never imply that a remote provider was used when it was not.

## Stop and clean up

Stop the foreground server with **Ctrl+C**. If you used a disposable checkout, remove that checkout only after confirming it contains no learner data you want to keep. Do not delete the normal project's data/ directory as a troubleshooting step.

## Claims to avoid

- Do not claim CEFR/IELTS proficiency, pronunciation accuracy, speech fluency scoring, measured learning gains, hiring likelihood, or placement probability.
- Do not call the product an AI interviewer or claim technical correctness grading.
- Do not claim a penetration test, security certification, public deployment approval, or multi-user readiness.
- Do not claim browser CI proves microphone hardware or real speech quality.
