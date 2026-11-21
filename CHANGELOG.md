# Changelog

All notable project changes are recorded here. This file tracks the source-checkout project; it does not imply that a distributable package or public release has been published.

## [0.3.0] — Unreleased development snapshot

### Added
- Stage 9 final UI integration checks across all six primary workspaces, responsive widths, navigation semantics, focus, reduced motion, and release acceptance documentation.
- Local learner profile, versioned English curriculum, Project Practice and Career interview studios.
- Learner-controlled Memory and revision, evidence-backed progress, goals, recommendations, and adaptive daily/weekly plans.
- Turn-based voice capture with editable transcripts, local Vosk STT, optional explicitly disclosed Groq STT, and local Piper/espeak-ng TTS.
- Curriculum/content validation, browser acceptance tests, backup export/restore, and local security/privacy controls.
- A source-checkout workflow helper for setup, start, health/readiness checks, verification, and optional voice setup.

### Security and privacy
- Removed an unused `httpx2` development dependency; test and optional Groq HTTP code use the maintained `httpx` package.
- Voice-model ZIP setup validates member paths and file types and caps expanded size before extracting downloaded content.
- Local HTML and static assets now revalidate with the browser after source-checkout updates, preventing stale cached UI code from surviving a pull.
- Loopback-only network boundary, bounded API/voice/restore request bodies, restrictive local SQLite permissions, and staged backup restore.
- No raw audio persistence, no telemetry, no automatic cloud sync, and no required paid service.
- Backups remain sensitive, unencrypted JSON. The project licence is not declared; redistribution is not authorised.

### Verification and limitations
- Stage 8 keyboard acceptance and full local verification passed on commit 55b9e11: 199 passed. Stage 9 exact-commit CI and target-device manual acceptance are tracked separately; no release is claimed.
- Latest recorded target-laptop full suite: 172 passed, 0 failed (2026-11-20).
- Exact code commit cff67fb passed GitHub Actions run 44754505687.
- Real-device microphone/STT/TTS, screen-reader/accessibility, restore power-loss, and learner-validation checks remain open.
- This is not a published release, validated language assessment, hiring/placement predictor, security certification, or production-scale service.
