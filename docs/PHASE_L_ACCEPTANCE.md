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
- [x] Keep the server bound to 127.0.0.1; start is foreground and Ctrl+C stops it.
- [x] Keep local voice model downloads explicit and outside application startup.
- [x] State the supported packaging boundary: source checkout is the supported install; wheel/binary packaging is not claimed because static assets and versioned content are repository-root resources and the project licence is unresolved.
- [ ] Complete a fresh install on the target Omarchy laptop from a clean checkout and verify text mode without voice dependencies.
- [ ] Verify clean update on a disposable checkout with a pre-update backup and post-update readiness check.
- [ ] Verify uninstall instructions preserve learner data unless the learner explicitly removes it.

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
| Target-laptop focused portability tests | python -m pytest -q tests/test_portability.py — 17 passed | Passed |
| Target-laptop full test suite | python -m pytest -q — 172 passed, 0 failed | Passed |
| Target-laptop filesystem modes | data/ 0700; SQLite file 0600 (recorded in Phase K) | Passed |
| Fresh target-device installation | Not yet performed on a clean checkout | Open |
| Full fresh-install restore drill | Automated coverage exists; manual disposable-data drill pending | Open |
| Real process-kill/power-loss restore drill | Not performed | Open |
| Voice/accessibility manual acceptance | Phase I checklist remains open | Open |
| Licence and redistribution | Project licence undeclared; no release archive/tag | Blocked |

## Release decision

Phase L implementation is in progress. Do not call this a release candidate yet. A release tag/archive is blocked until the project owner chooses a licence and the manual release gates are passed or explicitly deferred with an approved reason. The source-checkout workflow is the only supported packaging model. This document is an acceptance record, not a certification or promise of future hosting.
