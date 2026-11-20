# Prepped — Phase G release hardening and acceptance

**Status:** Engineering hardening in progress. Automated checks below are being expanded on `feature/learner-profile`. This document is the Phase G acceptance record; unchecked items are not complete.
**Scope:** Local, single-user release candidate only. This is not a public-hosting security certification, student pilot, or claim of market readiness.
**Constraints:** ₹0 mandatory cost; FastAPI + plain HTML/CSS/JavaScript + SQLite; no new service, paid API, hosted database, or framework migration.

## Phase G objective

Close material reliability, security, data-recovery, accessibility, and release-documentation gaps in the A–F implementation. Keep the existing architecture. Do not add product features merely to increase scope.

Phase G engineering can proceed while target-laptop A–F acceptance is pending. A release candidate cannot be signed off until the device-specific checks in this record are actually performed.

## 1. Automated engineering gates

- [ ] Final-commit GitHub Actions run is green.
- [x] Local-only Host validation rejects non-loopback authorities.
- [x] Host parsing rejects malformed authorities and invalid ports with HTTP 400 rather than an unhandled parsing error.
- [x] State-changing requests reject cross-origin, malformed, non-origin, user-info, and invalid-port Origin values with HTTP 403.
- [x] Valid same-origin browser requests and local command-line requests without an Origin header remain supported.
- [x] Backup restore rejects non-finite floats and integers outside SQLite's signed 64-bit range before touching the active database.
- [x] Deeply nested JSON restore input is converted to a controlled HTTP 400 response.
- [x] Readiness reports HTTP 503 when a required table is missing.
- [x] Invalid restore paths are tested to preserve existing learner data.
- [ ] Final browser acceptance passes for keyboard navigation, visible focus, form labels, workspace navigation, backup/restore, and mobile overflow.
- [ ] Python compilation, all JavaScript syntax checks, dependency installation, pip-audit, and the full pytest suite pass on the same final commit.

The checked items above describe code and tests added during Phase G; they do not imply the final CI run has passed. Record the final run URL, commit SHA, exact pass/skip count, warnings, and audit result here.

### Final automated evidence

- Commit: pending
- GitHub Actions run: pending
- Pytest: pending
- Python compilation: pending
- JavaScript syntax checks: pending
- pip-audit: pending
- Browser acceptance: pending

## 2. Network and application security

- [x] The documented server binds to `127.0.0.1`; the app is not intended for LAN or public access.
- [x] Host allowlisting and same-origin checks are implemented as defence-in-depth.
- [x] Security headers and API `Cache-Control: no-store` are implemented.
- [x] Malformed Host/Origin parsing is handled without leaking tracebacks.
- [ ] Review all state-changing routes for input bounds and expected error responses.
- [ ] Verify no permissive CORS configuration, debug server, public tunnel, or external deployment instructions have been introduced.
- [ ] Verify secrets, local databases, backups, personal answers, and voice models are not tracked by Git.

### Explicit security boundary

Prepped has no user authentication, multi-user isolation, account system, CSRF token framework, encrypted backup format, or production deployment model. Host/Origin checks are not a substitute for those controls. Do not expose this build through a LAN, reverse proxy, tunnel, or public internet endpoint.

## 3. Data integrity, backup, and recovery

- [x] Restore validates format/schema/table/column sets, scalar values, record limits, foreign keys, and staged SQLite integrity before replacement.
- [x] Restore requires explicit user confirmation and is a full replacement, not a merge.
- [x] Numeric edge cases and deeply nested JSON have regression tests.
- [x] Readiness checks SQLite quick-check, required tables, and curriculum loading.
- [ ] Run an export/restore rehearsal on a disposable target-laptop database.
- [ ] Confirm a failed restore leaves the original database and learner data unchanged on the target laptop.
- [ ] Confirm the backup file can be kept separate from the repository and is understood to be unencrypted JSON.

Never rehearse restore against the only copy of real learner data. Keep an untouched copy before any restore test.

## 4. Browser, accessibility, and responsive acceptance

Automated browser tests are useful regression evidence, not a substitute for assistive-technology review.

- [x] Native focus-visible styling exists.
- [x] Primary profile fields have associated labels.
- [x] Keyboard-only navigation and a narrow 375 px viewport have browser regression tests.
- [ ] Complete keyboard-only navigation through Home, Learning, Memory, Career, Progress, History, forms, dialogs, and restore controls.
- [ ] Complete screen-reader review with Orca or another available screen reader: headings, landmarks, labels, button names, status announcements, errors, and expanded/collapsed states.
- [ ] Check 200% zoom and 320/375/768 px widths; confirm no clipped controls, horizontal page scrolling, or inaccessible dialogs.
- [ ] Check contrast and visible focus in the actual browser theme and display environment.
- [ ] Confirm reduced-motion preferences do not make navigation or feedback unusable.

Core CSS text/status tokens were contrast-checked against the dark panel during the code audit: primary text 15.46:1, muted text 7.04:1, accent 14.36:1, and danger 9.86:1. This is a token-level calculation, not a complete WCAG audit of every rendered state.

## 5. Voice, privacy, and failure behaviour

- [ ] Confirm typed practice and lessons remain usable with all voice engines unavailable.
- [ ] On the target laptop, verify microphone permission denial, record/stop, editable transcript, session submission, and recording cancellation on navigation.
- [ ] Verify local Vosk and local TTS only when the relevant optional models/tools are installed.
- [ ] If Groq is explicitly configured, verify the disclosure appears before microphone permission and use only non-sensitive test speech.
- [ ] Confirm no raw audio file is retained by Prepped.
- [ ] Record browser, OS, engine availability, and observed errors. Do not infer Indian-English accuracy from synthetic speech or mocked API tests.

No speech-recognition accuracy, pronunciation score, learning gain, or placement outcome is claimed by this phase.

## 6. Performance and resource observations

No formal performance benchmark is claimed yet.

- [ ] On the target laptop, record cold and warm startup time.
- [ ] Record representative lesson/catalog and progress response times.
- [ ] If voice is tested, separately record model load, transcription, and TTS timings with engine/model and sample description.
- [ ] Record peak process memory and machine/browser/Python versions.
- [ ] Repeat observations enough times to report a range or median; label single runs as observations, not benchmarks.
- [ ] Confirm the app remains responsive on the target machine with its normal memory constraints.

Do not add infrastructure or background workers to solve unmeasured performance concerns.

## 7. Fresh install and release documentation

- [ ] Fresh clone/install using `docs/INSTALL.md` on the target laptop.
- [ ] Start the app on loopback and verify `/api/health` and `/api/ready`.
- [ ] Complete a disposable backup/recovery rehearsal.
- [ ] Review README, Current State, Complete Roadmap, Install, Voice, Release Hardening, and this record for consistent status and commands.
- [ ] Confirm all product claims match implemented and tested behaviour.
- [ ] Confirm student pilot, device checks, and voice accuracy remain unclaimed until observed.

## Release-candidate exit criteria

Phase G engineering may be called implementation-complete only when the final commit has a green full CI run, all automated regression gates pass, security/dependency findings are resolved or documented, and the release documentation is consistent.

The product may be called a locally accepted release candidate only after the target-laptop fresh install, learner journeys, backup/recovery, voice checks (where optional tools are installed), keyboard/screen-reader, contrast, responsive, and privacy checks have been performed and recorded.

A student pilot is optional and separate. A public or multi-user release is out of scope.
