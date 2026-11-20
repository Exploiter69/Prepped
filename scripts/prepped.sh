#!/usr/bin/env bash
# Small source-checkout helper. Run as: bash scripts/prepped.sh <command>
# It never exposes the server beyond loopback and never resets learner data.
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
VENV="$ROOT/.venv"
PYTHON="$VENV/bin/python"
PORT="$(printenv PREPPED_PORT || printf '8000')"
COMMAND=help
if (( $# > 0 )); then COMMAND="$1"; fi

usage() {
  cat <<'EOF'
Prepped local workflow

  bash scripts/prepped.sh setup        Create .venv; install app, dev and browser-test extras
  bash scripts/prepped.sh start        Run on 127.0.0.1 (foreground; Ctrl+C to stop)
  bash scripts/prepped.sh check        Check health, readiness and voice status
  bash scripts/prepped.sh verify       Compile, lint content, check JS/dependencies, run pytest
  bash scripts/prepped.sh voice-setup  Explicitly install optional local voice engines/models
  bash scripts/prepped.sh help         Show this help

Environment:
  PREPPED_PORT=8000                    Local port for start/check (default 8000)
  PYTHON=python3                        Python used by setup (default python3)

Safety:
  - The server is always bound to 127.0.0.1.
  - No command deletes, resets, migrates backwards, or exports learner data.
  - Back up learner data in the Progress UI before updating the checkout.
EOF
}

die() { printf 'Prepped: %s\n' "$*" >&2; exit 1; }

valid_port() {
  [[ "$PORT" =~ ^[0-9]+$ ]] || die "PREPPED_PORT must be an integer from 1 to 65535."
  (( PORT >= 1 && PORT <= 65535 )) || die "PREPPED_PORT must be an integer from 1 to 65535."
}

need_venv() {
  [[ -x "$PYTHON" ]] || die "No project .venv found. Run: bash scripts/prepped.sh setup"
}

case "$COMMAND" in
  help|-h|--help)
    usage
    ;;
  setup)
    SETUP_PYTHON="$(printenv PYTHON || printf 'python3')"
    command -v "$SETUP_PYTHON" >/dev/null 2>&1 || die "Python 3.11+ is required."
    "$SETUP_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else "Python 3.11 or newer is required.")'
    cd "$ROOT"
    "$SETUP_PYTHON" -m venv "$VENV"
    "$PYTHON" -m pip install -e ".[dev,browser-test]"
    "$PYTHON" -m playwright install chromium
    printf '\nSetup complete. Start with: bash scripts/prepped.sh start\n'
    ;;
  start)
    need_venv
    valid_port
    cd "$ROOT"
    exec "$PYTHON" -m uvicorn prepped.main:app --host 127.0.0.1 --port "$PORT"
    ;;
  check)
    valid_port
    need_venv
    "$PYTHON" - "$PORT" <<'PY'
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

base = f"http://127.0.0.1:{sys.argv[1]}"
for endpoint in ("/api/health", "/api/ready", "/api/voice/status"):
    try:
        with urlopen(base + endpoint, timeout=3) as response:
            payload = json.loads(response.read())
            print(f"{endpoint}: HTTP {response.status} — {payload}")
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{endpoint}: check failed ({exc}). Is Prepped running locally?")
PY
    ;;
  verify)
    need_venv
    cd "$ROOT"
    "$PYTHON" -m compileall -q prepped
    for file in static/*.js; do node --check "$file"; done
    "$PYTHON" -m prepped.content_lint
    "$PYTHON" -m pip check
    "$PYTHON" -m pytest -q
    ;;
  voice-setup)
    cd "$ROOT"
    shift || true
    exec bash scripts/setup_voice.sh "$@"
    ;;
  *)
    usage >&2
    die "Unknown command: $COMMAND"
    ;;
esac
