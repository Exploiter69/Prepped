# Phase K — Security, Privacy, Data Protection & Reliability

**Status:** Engineering controls and regression coverage implemented on the current branch; local and exact-commit CI verification are pending until the user runs the branch checks and GitHub Actions completes. Manual disk/permission/interruption recovery rehearsal remains open. This is not a security certification.

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

- Direct dependency roles and version ranges are documented in pyproject.toml.
- CI runs pip-audit against the resolved non-editable environment.
- CI produces pip-audit.json and dependency-licenses.json artifacts (30-day retention) using pip-licenses.
- Review the generated artifact for the exact workflow run. Optional model files are separately licensed; do not redistribute them without checking their own terms.
- There is no lockfile; repeatable resolution is not claimed.

## Automated acceptance matrix

| Requirement | Automated coverage / implementation | Status before user run |
|---|---|---|
| Loopback Host and actual peer | Host/Origin tests plus remote-peer spoof regression | Implemented; run pending |
| Request size bounds | 1 MiB JSON, 12 MiB voice, 25 MiB restore ASGI limits | Implemented; run pending |
| File permissions and symlink | POSIX 0700/0600 assertions, symlink/non-regular rejection | Implemented; run pending |
| SQL transaction rollback | Process-level exception rollback and subsequent integrity check | Implemented; run pending |
| Restore validation/rollback | Existing malformed, numeric, nested, size, row, FK and schema-compatibility tests | Existing coverage; run pending |
| Deletion cascades | Session answers, Career turns, Memory reviews | Implemented; run pending |
| Safe DOM sinks | Static test across all learner-facing JS modules | Existing coverage; run pending |
| Voice data disclosure | Existing adapter/status/error tests; raw audio remains in memory | Existing coverage; run pending |
| Dependency vulnerabilities | CI pip-audit JSON output | CI pending |
| Dependency licences | CI full installed-distribution licence inventory | CI pending |

## Manual acceptance — must use disposable data

- [ ] Verify default data/ mode 0700 and DB mode 0600 on the target Linux machine.
- [ ] On a disposable copy, simulate an unwritable data directory and confirm a clear startup failure without modifying unrelated files.
- [ ] On a disposable copy, approach disk exhaustion and record the SQLite/API error and recovery behaviour; do not use the only live DB.
- [ ] Interrupt a restore while using a disposable DB, then check /api/ready, SQLite integrity, and restore from a trusted backup.
- [ ] Upgrade a copy of a schema-3 database to current schema and verify preserved profile, sessions, answers, and foreign keys.
- [ ] Verify remote Groq disclosure and provider selection only if the optional key is configured; never use confidential audio.
- [ ] Inspect the exact CI dependency audit and licence artifacts; record any CVE or licence exception with a disposition.
- [ ] Recheck backup confidentiality, delete/cascade semantics, and the limitations in this document.

## Exit decision

Phase K may be marked engineering-complete only when the exact-commit local tests and GitHub Actions pass, dependency and licence artifacts have been reviewed, and there is no knowingly unresolved critical/high-severity issue. Manual disposable-data disk/permission/interruption tests must be recorded as passed or explicitly unavailable with reason before calling the local release candidate accepted.

No third-party penetration test, legal review, secure-erasure guarantee, security certification, or public deployment approval is claimed.
