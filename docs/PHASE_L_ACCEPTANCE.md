# Phase L — Release Candidate, Packaging, Documentation & Operations

**Target:** a reproducible, zero-cost, local single-user release candidate from a source checkout. No public deployment, LAN mode, account system, paid service, hosted database, or commercial-platform claim is in scope.

**Starting point:** Phase K engineering verification is complete on cff67fb; the target laptop reports 172 passed and the exact code commit passed GitHub Actions run 44754505687. This does not close Phase I or Phase J manual/content gates and is not release sign-off.

## L0 — Release definition and scope

- [x] Define the supported product mode: local, single learner, loopback-only; text mode is core and voice engines are optional.
- [x] Define the cost boundary: ₹0 required runtime spend; no required API keys, subscriptions, hosting, analytics, or usage-based service.
- [x] State explicit non-goals: public/LAN deployment, reverse proxy/tunnel, multi-user accounts, production operations, proficiency certification, hiring/placement prediction, and validated learning gains.
- [x] Record project version as 0.3.0 in pyproject.toml; add an Unreleased changelog entry.
- [ ] Create a release tag/archive only after the release gate is accepted and the owner has resolved the project licence.
- [x] Freeze scope to reliability, packaging/documentation, accessibility and release blockers; new features require a separate decision.

## L1 — Installation and packaging

- [x] Document clean source-checkout installation for Python 3.11+, local SQLite, browser, and optional voice prerequisites.
- [x] Add a small source-checkout helper for setup, start, health/readiness checks, full verification, and explicit optional voice setup.
- [x] Add shell syntax validation in CI and smoke tests for helper help/invalid-command behaviour.
- [x] Keep the server bound to 127.0.0.1; start is foreground and Ctrl+C stops it.
- [x] Keep local voice model downloads explicit and outside application startup.
- [x] State the supported packaging boundary: source checkout is the supported install; wheel/binary packaging is not claimed because static assets and versioned content are repository-root resources and the project licence is unresolved.
- [ ] Complete a fresh install on the target Omarchy laptop from a clean checkout and verify text mode without voice dependencies.
- [x] Document safe fast-forward update with pre-update backup, clean-working-tree check, and post-update readiness verification.
- [x] Document uninstall choices so removing the virtual environment preserves data/ and removing the checkout requires a private export first.
- [ ] Perform the documented update/uninstall rehearsal on a disposable target-laptop checkout.

## L2 — Runtime operations and observability

- [x] Document health/readiness and optional voice status checks.
- [x] Keep learner answers, transcripts, recordings, and provider keys out of application logs; unexpected voice errors log only the exception class.
- [x] Document database location, permissions, backup sensitivity, restore replacement semantics, and recovery warnings.
- [x] Add troubleshooting and a repeatable local demonstration.
- [ ] Record fresh target-laptop startup time, idle/active memory, representative learning/progress query observations, and local voice latency with conditions. These are observations, not performance benchmarks.
- [ ] Review the complete manual checklist on the target browser/device, including keyboard, screen reader, contrast, zoom, narrow screen, microphone permission, STT/TTS and text fallback.

## L3 — Data portability and recovery operations

- [x] Document backup format version 1 and SQLite schema version 4, included learner records, and unencrypted sensitive JSON handling.
- [x] Document full-replacement restore, pre-restore backup, and incompatible-version behaviour.
- [x] Add automated staged-restore, validation-failure, interrupted-worker, trusted-backup recovery, and integrity/foreign-key tests.
- [ ] Run a complete fresh-install recovery drill on disposable data using an exported backup and verify /api/ready plus SQLite integrity after restore.
- [ ] Run a real process-kill/power-loss restore interruption rehearsal on disposable data; never use the only learner database.

## L4 — Release quality and demonstration

- [ ] Complete [UI Stage 9 final acceptance](UI_STAGE_9_ACCEPTANCE.md): exact-commit CI, target-laptop verification, shared-shell accessibility, responsive/zoom/reduced-motion checks, and integrated learner journeys. Record unavailable checks as explicit deferrals; do not convert implementation commits into release sign-off.

- [x] Keep clean-checkout CI for compilation, JavaScript syntax, content lint, dependency consistency, vulnerability audit, Chromium installation, pytest, and browser acceptance.
- [x] Add a deterministic offline text-mode demo guide.
- [x] Add an Unreleased changelog and record exact verification evidence.
- [x] Document product limitations, privacy, local deployment boundary, optional voice and backup recovery.
- [ ] Complete Phase I target-device voice acceptance and Phase J human content/accessibility review, or explicitly defer them with reason in a release review.
- [ ] Complete a clean-install browser walkthrough and manual accessibility checks on the claimed target platform.
- [ ] Record exact release commit, CI run, local pass/skip counts, environment, manual findings, and unresolved risks in a release review.

## L5 — Deployment boundary

- [x] Keep default server command bound to loopback.
- [x] State that LAN/public hosting, reverse proxies, tunnels, multi-user isolation, and authentication are unsupported.
- [x] Keep the core text flow independent of paid APIs and remote speech providers.
- [x] Require a separate approved architecture, threat model, privacy/legal review, cost model, and operations plan before any future hosted mode.

## Verification record

| Check | Evidence | Status |
|---|---|---|
| Phase K exact code CI | GitHub Actions run 44754505687, commit cff67fb | Passed |
| Phase L helper/CI verification | GitHub Actions run 44756776414, commit a599d2c; shell syntax, compile, JS, content lint, dependency audit, Chromium and pytest | Passed: 172 passed, 2 optional voice skips |
| Target-laptop focused portability tests | python -m pytest -q tests/test_portability.py — 17 passed | Passed |
| Target-laptop full test suite (2026-11-20) | `bash scripts/prepped.sh verify` — content validation passed; 174 passed, 0 failed, 162.34s | Passed |
| Target-laptop filesystem modes | data/ 0700; SQLite file 0600 (recorded in Phase K) | Passed |
| Target-laptop helper health/readiness/voice check (2026-11-20) | `bash scripts/prepped.sh check`: health 200, ready 200, local Vosk STT and Piper TTS available; privacy and fallback status reported | Passed |
| Fresh target-device installation | Not yet performed on a clean checkout | Open |
| Full fresh-install restore drill | Automated coverage exists; manual disposable-data drill pending | Open |
| Real process-kill/power-loss restore drill | Not performed | Open |
| Voice/accessibility manual acceptance | Phase I checklist remains open | Open |
| Licence and redistribution | Project licence undeclared; no release archive/tag | Blocked |

## Release decision

Phase L engineering/documentation implementation is in progress. The source helper and its smoke tests pass in GitHub Actions [run 44756776414](https://github.com/Exploiter69/Prepped/actions/runs/44756776414) (172 passed, 2 optional voice skips). On 2026-11-20, the target laptop's `prepped.sh check` returned HTTP 200 for health, readiness and voice status, with local Vosk and Piper available; `prepped.sh verify` passed content validation and 174 tests in 162.34 seconds. This verifies endpoint readiness and installed engines, not actual microphone capture, speech recognition quality, or audible playback. Do not call this a release candidate yet. A release tag/archive is blocked until the project owner chooses a licence and the manual release gates are passed or explicitly deferred with an approved reason. The source-checkout workflow is the only supported packaging model. This document is an acceptance record, not a certification or promise of future hosting.
