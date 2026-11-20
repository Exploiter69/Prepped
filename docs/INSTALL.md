# Prepped — clean local installation and recovery

**Target:** local single-user development on Linux, including Omarchy/Arch.  
**Automated CI environment:** Ubuntu 24.04, Python 3.11, SQLite, Chromium.  
**Required operating cost:** ₹0. Python, FastAPI, SQLite, browser testing, and all core learning flows run locally.

## Requirements

- Python 3.11 or newer.
- A modern Chromium- or Firefox-based browser.
- SQLite through Python's standard library; no separate database server.
- Git for source checkout.

Optional voice support:
- `ffmpeg` to decode browser-recorded audio.
- Vosk plus an explicitly installed local model for offline STT, or an explicitly configured Groq key for remote STT.
- Piper or `espeak-ng` for local TTS.
- Voice dependencies and model weights are optional; no model is downloaded at startup. See [VOICE.md](VOICE.md).

## Fresh install

From a clean checkout:

```bash
git clone https://github.com/Exploiter69/Prepped.git
cd Prepped
git switch feature/learner-profile
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,browser-test]"
python -m playwright install chromium
```

The application runtime itself needs only the required dependencies from `pyproject.toml`; the `dev` and `browser-test` extras are for automated verification. Do not install optional voice extras unless you intend to test voice.

## Start the local application

```bash
source .venv/bin/activate
python -m uvicorn prepped.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Keep the server bound to loopback. Do not use `--host 0.0.0.0`, a LAN address, a public reverse proxy, or an internet-facing tunnel. The app intentionally accepts only local Host values and same-origin state-changing requests.

Useful local checks:

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://127.0.0.1:8000/api/ready
curl -fsS http://127.0.0.1:8000/api/voice/status
```

The default database is `data/prepped.sqlite3`. The `data/` directory and SQLite files are ignored by Git. Never add the database, backup files, `.env`, API keys, personal answers, or voice models to a commit.

## Verify the checkout

```bash
python -m compileall -q prepped
node --check static/app.js
node --check static/voice.js
node --check static/learning.js
node --check static/memory.js
node --check static/career.js
node --check static/progress.js
python -m pytest -q
```

The browser-test extra and Chromium are needed for the Playwright tests. GitHub Actions runs the same compilation, JavaScript syntax, dependency installation, Chromium setup, and pytest checks on a clean checkout.

## Export a backup

1. Open **Progress**.
2. Choose **Download local backup**.
3. Keep the downloaded JSON file somewhere private and separate from the repository.

The backup contains the local profile, practice sessions and answers, lesson attempts and events, learning-memory items and review history, career sessions and turns, learner goals, and dismissed recommendation preferences. It does not contain environment variables, API keys, speech models, or application source code.

Backups contain personal text. They are unencrypted JSON; protect them as you would protect your private notes. Do not upload them to public repositories, paste them into public issue trackers, or share them with other people unless you intentionally want to disclose the contents.

## Restore a backup

1. If the current database contains anything you may want later, export it first.
2. Open **Progress** and choose **Choose backup to restore**.
3. Select a Prepped backup JSON file.
4. Read and confirm the replacement warning.

Restore replaces all current local learner data with the backup. It is not a merge. Prepped validates the format, schema version, table/column set, record types, SQLite constraints, and foreign-key relationships in a temporary database before replacing the active database. A failed validation leaves the current database untouched.

The current backup format version is 1 and database schema version is 4. A backup from a future or incompatible schema is rejected rather than guessed or partially imported. Keep a copy of the original file before attempting migration between future releases.

## Supported environment and boundaries

- The reproducible automated environment is Ubuntu 24.04 + Python 3.11 + SQLite + Chromium.
- The intended personal development environment includes Linux desktops such as Omarchy/Arch with Python 3.11 or newer and a current browser.
- Target-laptop microphone permission, local speech engines, TTS output, and device-specific responsive behaviour still require manual acceptance on the actual laptop.
- No account, analytics service, hosted database, remote LLM interviewer, paid API, or internet connection is required for text practice, lessons, interview studios, progress, or backup/restore.
- If Groq Whisper is explicitly configured, recorded audio is sent to Groq for transcription. The app does not persist raw audio. See [VOICE.md](VOICE.md) and [ADR-003](ADR-003-GROQ-WHISPER-TRANSCRIPTION.md).
- Progress counts are evidence of saved activity. They are not proficiency, confidence, learning gain, hiring likelihood, or placement predictions.
- The student usability pilot is future validation. No participant results are claimed.

## Recovery if the app will not start

- Keep the original database file untouched before attempting manual repair.
- Check `/api/ready` after startup; it checks the local SQLite integrity and required tables plus the versioned curriculum.
- Restore only from a backup you trust and have kept privately.
- Do not delete `data/prepped.sqlite3` as a generic troubleshooting step; it contains the learner's saved work.
- If the backup itself is the only copy, duplicate the file before trying restore.


## Local data protection

- The default data directory is created/restricted to POSIX mode 0700; the SQLite database is created/restricted to 0600. Existing default data-directory permissions are tightened on startup. This is a local filesystem safeguard, not encryption.
- Keep the operating-system account private and the disk protected. Anyone who can read files as the same OS user can read the database.
- Backups downloaded by the browser are unencrypted JSON. Their permissions and location are controlled by the browser/desktop environment, not by the server. Move them to a private location and do not commit/share them.
- Deleting records removes them from the live SQLite tables and dependent rows; it is not a forensic secure-erase guarantee for filesystem snapshots, old backups, or storage media.
- The server rejects non-loopback TCP peers even if they send a loopback Host header. Keep Uvicorn bound to 127.0.0.1; this does not make LAN/public deployment supported.
- JSON API request bodies are limited to 1 MiB, audio transcription uploads to 12 MiB, and backup restore to 25 MiB.
