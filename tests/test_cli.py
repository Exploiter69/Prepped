"""Smoke tests for the documented source-checkout helper."""
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "prepped.sh"


def test_local_helper_help_is_available_without_creating_a_venv() -> None:
    result = subprocess.run(
        ["bash", str(HELPER), "help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "setup" in result.stdout
    assert "127.0.0.1" in result.stdout
    assert "Ctrl+C to stop" in result.stdout


def test_local_helper_rejects_unknown_commands_without_side_effects() -> None:
    result = subprocess.run(
        ["bash", str(HELPER), "not-a-command"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Unknown command" in result.stderr
