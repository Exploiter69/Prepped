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
- Backup format version 1 and database schema version 3 are explicit; incompatible versions fail closed.

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
