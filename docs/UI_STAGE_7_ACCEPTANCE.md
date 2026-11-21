# UI Stage 7 — Dashboard next-step polish

## Implementation scope

- The first unfinished lesson in the learner's current route can be launched directly from the dashboard through the existing Learn runner.
- The dashboard offers an explicit refresh action and announces loading/partial-failure/success states politely.
- The completed-route state is clear, and responsive/reduced-motion styles are covered.

No API, database, curriculum, provider, dependency, or learner-data changes.

## Automated checks

Regression tests are in `tests/test_ui_stage7.py`. Run `bash scripts/prepped.sh verify` and record the exact result; a repository commit is not evidence of a laptop test pass.

## Manual acceptance — pending

- Start the dashboard's next lesson using keyboard and pointer; confirm the right lesson opens and answers save normally.
- Complete the current route and confirm the dashboard does not imply an unfinished lesson.
- Refresh normally and with one endpoint unavailable; verify polite status and usable partial content.
- Check desktop/mobile, zoom, focus, screen-reader announcements, and reduced motion.
- Confirm no learner data is lost or newly collected.
