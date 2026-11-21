#!/usr/bin/env bash
# Explicit, one-time local voice setup. Nothing here runs at application start.
#
# Usage:
#   ./scripts/setup_voice.sh            # Vosk STT + optional Piper TTS + Groq voice HTTP adapter + Piper voice
#   ./scripts/setup_voice.sh --stt-only # Vosk STT + Groq HTTP adapter; espeak-ng is the TTS fallback
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -z "${PYTHON:-}" ]; then
  if [ -x "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
  else
    PYTHON="python3"
  fi
fi
MODELS_DIR="$ROOT/models"
VOSK_MODEL="vosk-model-small-en-us-0.15"
VOSK_DIR="$MODELS_DIR/$VOSK_MODEL"
PIPER_DIR="$MODELS_DIR/piper"
PIPER_VOICE="en_US-lessac-medium"
INSTALL_PIPER=1

for arg in "$@"; do
  case "$arg" in
    --stt-only) INSTALL_PIPER=0 ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

echo "Prepped local voice setup"
echo "Repository: $ROOT"
echo "Python:     $($PYTHON --version 2>&1)"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "WARNING: ffmpeg was not found. Browser recordings need it to decode audio." >&2
  echo "         On Arch/Omarchy: sudo pacman -S ffmpeg" >&2
fi

if [ "$INSTALL_PIPER" -eq 1 ]; then
  echo "Installing Python voice extras (Vosk and optional Piper)..."
  "$PYTHON" -m pip install -e "$ROOT[voice,voice-piper,voice-cloud]"
else
  echo "Installing Python speech-to-text extra (Vosk)..."
  "$PYTHON" -m pip install -e "$ROOT[voice,voice-cloud]"
fi

mkdir -p "$MODELS_DIR"

if [ -d "$VOSK_DIR/am" ] && [ -d "$VOSK_DIR/conf" ] && [ -d "$VOSK_DIR/graph" ]; then
  echo "Vosk English model already present: $VOSK_DIR"
else
  echo "Downloading Vosk small English model (~40 MB compressed, ~68 MB on disk)..."
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  curl -fL --retry 3 -o "$tmp_dir/model.zip" \
    "https://alphacephei.com/vosk/models/$VOSK_MODEL.zip"
  PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" -m prepped.voice.model_archive "$tmp_dir/model.zip" "$MODELS_DIR"
  rm -rf "$tmp_dir"
  trap - EXIT
fi

if [ "$INSTALL_PIPER" -eq 1 ]; then
  if [ -f "$PIPER_DIR/$PIPER_VOICE.onnx" ]; then
    echo "Piper voice already present: $PIPER_DIR/$PIPER_VOICE.onnx"
  else
    echo "Downloading Piper voice $PIPER_VOICE (~61 MB)..."
    mkdir -p "$PIPER_DIR"
    if "$PYTHON" -m piper.download_voices --data-dir "$PIPER_DIR" "$PIPER_VOICE"; then
      echo "Piper voice installed."
    else
      echo "WARNING: Piper voice download failed. Spoken prompts will use espeak-ng if installed." >&2
    fi
  fi
else
  echo "Skipping Piper. Spoken prompts use espeak-ng when it is installed."
fi

if ! command -v espeak-ng >/dev/null 2>&1 && [ ! -f "$PIPER_DIR/$PIPER_VOICE.onnx" ]; then
  echo "WARNING: no local TTS is available. Install espeak-ng or rerun without --stt-only." >&2
  echo "         On Arch/Omarchy: sudo pacman -S espeak-ng" >&2
fi

echo
echo "Voice setup finished. Start Prepped with:"
echo "  $PYTHON -m uvicorn prepped.main:app --reload"
echo "Then open http://127.0.0.1:8000 and use /api/voice/status to check local engines."
