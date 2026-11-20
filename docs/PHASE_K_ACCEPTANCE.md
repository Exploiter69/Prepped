# Phase K — Security, Privacy, Data Protection & Reliability

**Status:** Engineering implementation and exact-commit GitHub Actions passed on commit f0d4dd14673392ea90787a7029873be11f89b69b ([run 44750831526](https://github.com/Exploiter69/Prepped/actions/runs/44750831526)): 168 passed, 2 skipped, 0 warnings. pip-audit scanned 73 resolved dependencies with 0 known vulnerabilities; pip-licenses produced 68 distribution records. User laptop verification and disposable-data recovery drills remain open. The repository's own licence is undeclared; no redistribution permission is implied. This is not a security certification.

**Scope:** local, single-user, loopback-only application. No LAN/public deployment, reverse proxy, tunnel, multi-user accounts, authentication, or hosted database is supported or authorised.

## Threat model and controls

| Area | Threat / abuse case | Control / evidence | Residual risk |
|---|---|---|---|
| Network | Remote peer spoofs a loopback Host header after accidental wildcard bind | Host allowlist plus actual TCP peer loopback check; regression test uses a non-loopback peer | A reverse proxy/tunnel or changed server topology invalidates assumptions; unsupported |
| Browser origin | Cross-origin state mutation, clickjacking, MIME sniffing, script injection | Same-origin Origin check; no CORS; CSP; frame denial; nosniff; no-store; safe text rendering regression test | Same-origin script compromise, malicious extension, local browser profile compromise |
| Request parsing | Oversized or malformed API bodies exhaust memory | General JSON API 1 MiB, voice 12 MiB, restore 25 MiB caps, including chunked bodies; validation tests | Local OS-level resource exhaustion remains possible |
| Filesystem | Database read by other local users; symlink substitution | Default data directory 0700, SQLite file 0600 on POSIX, reject symlink/non-regular DB target | Same OS account/root can read or alter files; ACLs, snapshots and backups are OS-managed |
| SQLite | Interrupted transaction, invalid references, corruption, migration drift | Rollback on BaseException, FK enforcement, busy timeout, trusted-schema off, readiness quick-check, staged restore integrity/FK checks | Hardware/filesystem failures and disk-full conditions still need manual rehearsal |
| Import/restore | Malformed, hostile, oversized, incompatible or referentially broken backup | Strict shape/type/column/schema checks, bounded size/rows/text/numbers, staged SQLite, explicit full replacement, existing DB preserved on validation failure | A structurally valid backup can still overwrite data after explicit confirmation |
| Remote STT | Accidental audio disclosure or key exposure | Groq requires explicit environment key; provider disclosure; no silent fallback; no raw-audio persistence; no key in status | Audio is sent to Groq when selected; current provider terms/retention apply |
| Logs/secrets | Transcript, answer, raw audio, provider key or exception details leak into logs | Voice unexpected errors log exception class only; credentials remain server-side; .env ignored | OS/process inspection and third-party tooling can see process environment |
| Dependencies | Known CVE, stale transitive dependency, unclear redistribution licence | CI pip-audit plus complete installed-package licence metadata inventory uploaded as artifact | Audit is point-in-time; no lockfile; model weights have separate licences |
| Local account | Malware or another process under the same user reads learner data | Loopback-only access and restrictive filesystem modes | A compromised local account is outside the app's security boundary |

## API and data-path review

- Main API uses bounded Pydantic fields and SQL parameters for learner values; dynamic SQL identifiers in portability are selected only from the fixed internal table/column lists derived from the application schema.
- Backup restore is the only JSON import path. It is size-limited, strict-schema validated, staged in a temporary SQLite DB, and checked for foreign keys and integrity before replacement.
- Voice upload is streamed under its own cap; decoding and optional remote STT occur in memory.
- Learner-controlled content is rendered as text; tests/test_release_hardening.py rejects unsafe HTML string sinks in the application scripts.
- Host and Origin validation, CSP, no CORS, no-store API headers, and controlled public voice errors are retained. Unexpected voice errors no longer log exception text or traceback.
- SQL foreign keys are enabled on each application connection. Session, Career session, and Memory deletion cascade to their dependent answer/turn/review rows.

## API and route review inventory

| Route group | Surface reviewed | Validation / safety boundary |
|---|---|---|
| Core practice | /api/health, /api/ready, scenario read, session create/list/read/answer/cancel/feedback/retry/delete | Pydantic answer limits, expected-question state checks, parameterized values, session deletion cascade |
| Learner profile | GET/PUT /api/profile | Enumerated goals/focus, bounded text and study-year validation |
| Learning | catalogue, recommendations, attempt create/read/response, diagnostic, progress | Versioned curriculum loader/linter, bounded exercise responses, stable lesson IDs, parameterized persistence |
| Learning memory | item list/create/read/update/status/dismiss/restore/delete, review queue/history/stats | Bounded front/back/source fields, fixed update-field allowlist, parameterized values, duplicate checks, review cascade |
| Progress and goals | overview, recommendation dismiss/restore, goal CRUD/archive/restore | Literal goal/recommendation enums, bounded text/counts, parameterized IDs and values |
| Adaptive intelligence | overview/catalogue, daily/weekly plans, item create/update, recommendation preferences | Date/range/enumeration validation, bounded plans and item fields, deterministic local logic |
| Career studios | catalogue, session create/list/read/answer/feedback/retry/delete | Versioned authored content, bounded answer length, fixed studio/difficulty IDs, session state checks, turn cascade |
| Voice | engine status, streamed transcription, local TTS | 12 MiB cap, 60-second decode bound, TTS text cap, explicit remote STT status/disclosure, timeout handling, no raw-audio files |
| Data portability | status/export/restore | Fixed table list, schema/column/type validation, 25 MiB/200,000-row caps, staged DB, integrity/FK checks |

SQL value inputs are parameterized. The few dynamic SQL identifiers are constrained to internal constants: Memory update fields are a fixed tuple; portability table names are a fixed tuple and column names come from the freshly initialized internal schema. No client-provided SQL identifier is accepted.

## Personal-data lifecycle

The complete inventory and retention/export/deletion/recipient table is maintained in RELEASE_HARDENING.md under Personal-data inventory and lifecycle.

Key decisions:
- Learner data is local in data/prepped.sqlite3; there is no telemetry or automatic cloud sync.
- Export contains personal text and remains unencrypted JSON. It excludes credentials, environment variables, raw audio and model weights.
- Saved records remain until the learner deletes them or removes the local data store; no automatic retention/expiry exists.
- Deletion cascades within the active DB but is not forensic erasure of backups, snapshots, or storage media.
- Optional Groq transcription sends the recording to Groq only when explicitly configured; local Vosk remains local.
- No raw audio is persisted by Prepped.

## Backup encryption decision

Application-level backup encryption is deferred. Adding encryption without a reliable recovery UX and key-loss policy risks making the only backup irrecoverable. Backups are clearly classified as sensitive, unencrypted JSON; protect them using OS account security, full-disk encryption, private storage and multiple trusted copies. This is an explicit residual risk.

## Dependency and licence evidence

- CI installs all declared extras: dev, browser-test, voice, voice-piper, and voice-cloud. The exact run scanned 73 resolved dependencies with pip-audit and reported zero known vulnerabilities.
- pip-licenses generated a 68-distribution JSON inventory (67 third-party distributions plus the local prepped package). The artifact is available from [workflow run 44750831526](https://github.com/Exploiter69/Prepped/actions/runs/44750831526), retained for 30 days.
- Notable licence metadata: Vosk 0.3.45 reports Apache Software License; Piper TTS 1.8.0 reports GPL-3.0-or-later; httpx2 2.16.2 reports BSD-3-Clause. Piper is optional and neither Piper nor Vosk model weights are bundled; model assets have separate licence terms.
- The local prepped 0.3.0 distribution reports UNKNOWN. The repository has no LICENSE file and pyproject.toml has no project licence declaration. Do not assume the project grants reuse or redistribution rights. The owner must choose and add a licence before distributing the package; this is an explicit unresolved owner decision, not an approved exception.
- There is no lockfile; repeatable dependency resolution is not claimed. GitHub Actions use Node 24 action releases (checkout v7.0.1, setup-python v7.1.0, upload-artifact v7.0.2). httpx2 is included in dev dependencies for Starlette TestClient, eliminating the prior httpx deprecation warning.

## Automated acceptance matrix

| Requirement | Automated coverage / implementation | Exact-commit CI status (f0d4dd1) |
|---|---|---|
| Loopback Host and actual peer | Host/Origin tests plus remote-peer spoof regression | Passed in CI; laptop run pending |
| Request size bounds | 1 MiB JSON, 12 MiB voice, 25 MiB restore ASGI limits | Passed in CI; laptop run pending |
| File permissions and symlink | POSIX 0700/0600 assertions, symlink/non-regular rejection | Passed in CI; laptop run pending |
| SQL transaction rollback | Process-level exception rollback and subsequent integrity check | Passed in CI; laptop run pending |
| Restore validation/rollback | Existing malformed, numeric, nested, size, row, FK and schema-compatibility tests | Passed in CI; laptop run pending |
| Deletion cascades | Session answers, Career turns, Memory reviews | Passed in CI; laptop run pending |
| Safe DOM sinks | Static test across all learner-facing JS modules | Passed in CI; laptop run pending |
| Voice data disclosure | Existing adapter/status/error tests; raw audio remains in memory | Passed in CI; laptop run pending |
| Dependency vulnerabilities | CI pip-audit scanned 73 resolved dependencies | 0 known vulnerabilities |
| Dependency licences | CI inventory reviewed: 68 distributions; local prepped package UNKNOWN; optional Piper GPL-3.0-or-later | Reviewed; project licence decision required before redistribution |

## Manual acceptance — remaining target-device checks

Automated failure simulations and regression tests are recorded in the exact CI run. The remaining checks below must use disposable data and must not endanger the only learner database.

- [ ] On the target Linux machine, verify default data/ mode 0700 and DB mode 0600 after starting Prepped.
- [x] POSIX permission-denied simulation: a custom read-only database directory rejects creation cleanly; passed in CI. Target-device confirmation is optional.
- [x] SQLite disk-full simulation: PRAGMA max_page_count forces a bounded database-full failure; transaction rolls back and integrity_check remains ok. No real filesystem was filled.
- [ ] Interrupt a restore while using a disposable DB, then check /api/ready, SQLite integrity, and restore from a trusted backup.
- [x] Schema-3 upgrade regression test: preserved session/answer data, adaptive tables recreated, foreign keys and integrity pass in CI. A real user DB must still be backed up before any local upgrade.
- [ ] Verify remote Groq disclosure/provider selection only if the optional key is already configured; never use confidential audio.
- [x] CI audit artifacts reviewed: 0 known vulnerabilities across 73 dependencies; 68 licence records; Piper GPL-3.0-or-later; project package UNKNOWN.
- [ ] Recheck backup confidentiality, delete/cascade semantics, and the limitations in this document.
- [ ] Choose and declare a project licence before any package/source redistribution; do not treat the current UNKNOWN metadata as permission.

## Exit decision

Phase K may be marked engineering-complete only when the exact-commit local tests and GitHub Actions pass, dependency and licence artifacts have been reviewed, and there is no knowingly unresolved critical/high-severity issue. Manual disposable-data disk/permission/interruption tests must be recorded as passed or explicitly unavailable with reason before calling the local release candidate accepted.

No third-party penetration test, legal review, secure-erasure guarantee, security certification, or public deployment approval is claimed.
