# Prepped — release hardening and security notes

**Scope:** local single-user prototype. This is an engineering checklist and threat-boundary record, not a third-party security audit or a claim that the application is safe for public multi-user hosting.

## Network boundary

- The documented server command binds Uvicorn to `127.0.0.1`.
- The application rejects Host headers other than loopback names and the in-process test host.
- State-changing requests with an Origin header must match both the request scheme and authority; malformed authorities, ports, user-info, and non-origin path/query/fragment values are rejected.
- No permissive CORS middleware is installed.
- API responses use `Cache-Control: no-store`.
- Security response headers include CSP, frame denial, MIME sniffing protection, a restrictive referrer policy, and a permissions policy that allows microphone use only from the app's own origin.
- The Content Security Policy permits only same-origin scripts/connections and the local blob/media needs of recorded audio and generated speech.

**Do not expose the prototype to a LAN, public internet, reverse proxy, or tunnel.** There is no user authentication, multi-user isolation, CSRF token system, or production deployment model. The local Host/Origin checks are defence-in-depth for the documented single-user loopback deployment, not a substitute for authentication or a full threat model.

## Input and upload boundaries

- API request models validate enumerations, text lengths, counts, and required fields.
- Practice and interview answers have bounded text lengths.
- Memory cards have bounded front/back/source text lengths and normalized duplicate handling.
- Voice routes enforce content type, decode/error handling, and bounded upload size before processing.
- Backup restore caps request size at 25 MiB and record count at 200,000; only known tables/columns and scalar values are accepted. Non-finite floats, integers outside SQLite's signed 64-bit range, and excessively nested JSON are rejected.
- Backup restore is staged in a temporary SQLite database and checks schema version, constraints, integrity, and foreign keys before replacing the current database.
- Restore requires explicit UI confirmation and is a full replacement, not a merge.
- Browser rendering uses text nodes/textContent for learner-controlled content; do not insert user text through `innerHTML`.

## Secrets and private data

- Groq credentials, when used, stay in the server environment and are never returned to the browser.
- `.env`, local databases, backup files, and voice model files are ignored by Git.
- No raw microphone recording is persisted by Prepped.
- Groq mode transmits the recording to Groq for transcription; local Vosk mode does not send audio to a remote transcription provider.
- Exported backups contain the learner's written answers, profile, notes, and practice history. They are unencrypted JSON and must be stored privately.
- No analytics, telemetry, external database, or automatic upload of learner progress is included.

## Data integrity and recovery

- SQLite foreign keys are enabled for application connections.
- Schema changes are additive and use the existing database.
- The readiness endpoint checks SQLite quick-check, required tables, and curriculum loading.
- Backup restore validates against a fresh staged database and preserves the active database when validation fails.
- Backup format version 1 and database schema version 4 are explicit; incompatible versions fail closed.

## Dependencies and supply chain

- Runtime dependencies are declared in `pyproject.toml`; voice and browser-test dependencies remain optional extras.
- GitHub Actions installs from a clean checkout and runs Python compilation, JavaScript syntax checks, and pytest with Chromium.
- Dependency vulnerability scanning is run in CI using pip-audit; findings must be reviewed and remediated before a release candidate is accepted.
- Do not commit generated model weights, databases, backups, build artifacts, or secrets.

## Accessibility and responsive acceptance

- All navigation and forms use native buttons, labels, inputs, and status/alert regions.
- Keyboard focus is visibly styled.
- Progress bars expose accessible names and numeric values.
- Learner data is rendered as text, not interpreted markup.
- Chromium acceptance covers navigation, goals, backup download/restore, and workspace transitions.
- Real keyboard-only, screen-reader, contrast, and target-device responsive checks remain manual release gates.

## Phase G implementation notes

- Host and Origin parsing now validates authority syntax, rejects malformed IPv6/ports, user-info, and non-origin path/query/fragment values, and returns controlled 400/403 responses.
- Backup restore rejects non-finite floating-point values, integers outside SQLite's signed 64-bit range, and excessive JSON nesting before replacing active learner data.
- Regression tests cover valid local clients, malformed Host/Origin headers, invalid backup numerics, nested JSON, restore rollback, and missing-table readiness.
- Browser acceptance now includes keyboard-only navigation to the profile form, visible focus, primary form labels, and a 375 px viewport overflow check across Home, Learning, Career, and Progress.
- The final Phase G CI run and target-device acceptance are tracked in [PHASE_G_ACCEPTANCE.md](PHASE_G_ACCEPTANCE.md).

These are implementation changes, not a completed security audit or target-device sign-off. See the Phase G record for outstanding checks.

## Claims and non-goals

Prepped does not provide a validated language assessment, pronunciation/accent score, emotion/personality inference, technical correctness grading, recruiter rating, placement probability, or measured learning gains. Progress is based on saved activity and linked lesson evidence only. The student usability pilot has not been run; no results or participant sample are claimed.


## Final automated verification

Phase G.1 microphone lifecycle regressions and Phase H integration passed in [GitHub Actions run 44732997261](https://github.com/Exploiter69/Prepped/actions/runs/44732997261): 134 passed, 2 optional espeak-ng skips, 1 Starlette TestClient deprecation warning. Manual Omarchy/device and learner acceptance remain open.


## Phase K — security, privacy, and reliability review

### Threat model and trust boundaries

| Asset / boundary | Threat | Existing or added mitigation | Residual risk |
|---|---|---|---|
| Loopback HTTP API | LAN client reaches a mistakenly exposed server or spoofs Host: localhost | Documented bind is 127.0.0.1; Host syntax/allowlist and actual TCP peer loopback are both checked; same-origin state changes are enforced | No authentication; reverse proxies, tunnels, LAN/public access, and multi-user operation remain unsupported |
| Browser origin | Cross-site state changes, framing, MIME sniffing, content injection | Origin scheme/authority validation, no CORS middleware, CSP, frame denial, nosniff, no-store; learner content uses text nodes and static test rejects HTML string sinks | A compromised same-origin script/browser extension or local browser profile can act as the user |
| API input | Oversized, malformed, deeply nested, or invalid values | 1 MiB general API body cap, 12 MiB audio cap, 25 MiB restore cap; Pydantic bounds; explicit malformed-header and restore validation tests | Limits do not prevent resource exhaustion from a compromised local account or OS |
| Local files | Other local users read/replace the SQLite database or redirect it through a symlink | Default data directory mode 0700; DB regular-file mode 0600; DB symlink/non-regular targets rejected | Same OS account, root, malware, filesystem snapshots, and backups can still access data |
| SQLite | Partial writes, schema drift, foreign-key or migration defects | Per-connection FK enforcement, busy timeout, trusted-schema disabled, transaction rollback, quick/integrity checks, staged restore, additive idempotent migrations | Abrupt hardware failure, disk exhaustion, filesystem corruption, or concurrent external DB modification can still require restore |
| Backup import/export | Malicious or incompatible backup replaces learner data | Explicit full-replacement confirmation, strict format/schema/table/column/scalar checks, numeric bounds, record/byte limits, staged DB, FK/integrity checks, fail-closed legacy/future schema handling | Backup content is personal data and unencrypted; a valid malicious backup can still replace data if the learner confirms it |
| Optional remote STT | Audio is disclosed to a third party or provider request leaks credentials | Remote mode requires explicit server-side GROQ_API_KEY; UI/status discloses provider; no silent local-to-remote fallback; audio is processed in memory; API key is not returned to browser | Provider receives audio and handles it under its own current terms/retention; do not send confidential recordings |
| Secrets and dependencies | API key committed/logged; vulnerable or incompatible dependency installed | Environment-only key, Git ignore rules, voice errors log exception class only, CI pip-audit and full installed-package licence inventory | Environment variables are readable by the same OS account/process inspector; dependency audit is time-sensitive and not a guarantee |
| Compromised local account | Malware or another process under the same user reads or modifies all learner data | OS file modes and local-only binding reduce exposure to other local users/network peers | This threat is not containable inside a single-user app; OS account/device security is the trust root |

### Personal-data inventory and lifecycle

| Data | Purpose | Primary location | Retention / deletion | Export | External recipient |
|---|---|---|---|---|---|
| Optional learner profile fields | Choose a learner-controlled starting route | SQLite learner_profile in data/prepped.sqlite3 | Until edited or local profile/database is deleted; no automatic expiry | Included | None |
| Project practice sessions and answers | Practice and review submitted work | SQLite sessions, answers | Until learner deletes a session or database; answers cascade with session | Included | None |
| Lesson attempts, responses, activity events | Resume lessons and derive transparent progress | SQLite learning_attempts, learning_events | Until local data/database deletion; events cascade with their attempt where linked | Included | None |
| Learning memory and review history | Learner-approved personal revision | SQLite learning_memory, learning_memory_reviews | Until learner deletes an item; review rows cascade with item | Included | None |
| Career sessions and turns | Interview practice and retry history | SQLite career_sessions, career_turns | Until learner deletes a session; turns cascade with session | Included | None |
| Goals, recommendation dismissals, adaptive plans | Learner-owned planning and preferences | SQLite local tables | Until edited/deleted with local database; no automatic expiry | Included | None |
| Raw microphone recording | Transcription only | Browser memory and request memory; decoded in memory | Discarded after request; not persisted by Prepped | Not included | Groq only when remote STT is explicitly configured; otherwise none |
| Transcript text | Editable answer submission | Browser while editing; saved in the relevant learner-data table only after learner submits | Until the saved answer/session/attempt is deleted | Included when saved | Groq returns transcript when remote STT is used; provider receives the audio |
| Voice models and environment secrets | Local engine operation | User-managed models/ and process environment | Outside learner-data deletion/export; user-managed | Not included | No automatic upload; Groq key authenticates optional remote request |

**Deletion semantics:** API deletion cascades remove dependent rows from the active SQLite database. It does not erase exported backups, browser downloads, OS snapshots, filesystem journal remnants, or other copies. There is no automatic retention timer or telemetry.

### Backup encryption decision

Phase K does not add application-level backup encryption. A password-based scheme without a carefully designed recovery UX, tested key derivation, and a safe key-loss policy could make the only learner backup permanently unrecoverable. No encryption key is stored by Prepped. Therefore backups remain explicitly labelled sensitive, unencrypted JSON. Users should keep them in a private location, use full-disk encryption/OS account protections, and retain more than one trusted copy before a destructive restore. This is a documented residual risk, not a claim that file permissions encrypt backups.

### Dependency maintenance and licence review

- Required runtime direct dependencies: FastAPI and Uvicorn (ASGI server); SQLite is Python's standard library and has no separate service.
- Optional direct dependencies: Vosk for local STT, Piper TTS for local speech, httpx for optional Groq STT, Playwright for browser acceptance; pytest/httpx are development/test tools.
- Declared version ranges are bounded in pyproject.toml; there is no lockfile, so the resolved transitive set can change. CI audits the resolved install with pip-audit.
- CI generates JSON evidence for all installed distribution licence metadata using pip-licenses and uploads both the vulnerability and licence inventories as a 30-day workflow artifact. Review distribution metadata and upstream licence texts before redistributing optional packages or model weights.
- Optional Piper/Vosk model files are not bundled; each model's own licence and redistribution terms must be checked separately. No unresolved vulnerability or licence exception is pre-approved by this document; inspect the artifact for the exact commit/run.
- The repository currently has no LICENSE file and pyproject.toml declares no project licence; pip-licenses therefore reports the local prepped distribution as UNKNOWN. No reuse or redistribution permission should be inferred. The owner must choose and add a licence before distributing the package.
- Exact CI run 44750831526 scanned 73 resolved dependencies with pip-audit and found no known vulnerabilities. The 68-entry licence inventory records 67 third-party distributions and the local prepped package. Vosk 0.3.45 reports Apache Software License; Piper TTS 1.8.0 reports GPL-3.0-or-later; httpx2 2.16.2 reports BSD-3-Clause. Piper/Vosk are optional and no models are bundled. Review the workflow artifact before changing or redistributing these dependencies.
- CI installs every declared extra (dev, browser-test, voice, voice-piper, voice-cloud). The TestClient backend now uses httpx2 to remove the Starlette/httpx deprecation warning. GitHub Actions are on Node 24 action releases.

### Reliability verification and manual limits

Automated tests cover: rollback on a process-level exception, SQLite integrity and foreign-key checks, private DB modes and symlink rejection on POSIX, remote-peer rejection, malformed Host/Origin and Content-Length values, request-size caps, staged restore rejection without replacement, version-3 backup migration, cascade deletion, and readiness failure when required tables are missing.

Still requires target-machine rehearsal before a release candidate: deliberately test a full/near-full disk on disposable data; deny write permission to a disposable data directory; interrupt a disposable restore process; perform an actual old-schema database upgrade; and verify restore/recovery from a second trusted backup. Never perform destructive tests on the only copy of real learner data.

This is an engineering threat model and control review, not a penetration test, legal privacy review, dependency guarantee, or security certification.

## Phase K acceptance tracking

See [PHASE_K_ACCEPTANCE.md](PHASE_K_ACCEPTANCE.md) for the itemised implementation/test matrix, exact-commit evidence, residual risks, and manual acceptance record.
