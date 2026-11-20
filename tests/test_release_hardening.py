"""Static release guardrails for learner-controlled content and local data."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _relative_luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def _contrast_ratio(first: str, second: str) -> float:
    light, dark = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_learner_content_is_not_written_through_html_string_sinks() -> None:
    scripts = (
        "app.js",
        "voice.js",
        "learning.js",
        "memory.js",
        "career.js",
        "progress.js",
    )
    forbidden = re.compile(
        r"\.(?:innerHTML|outerHTML)\s*(?:=|\+=)|"
        r"\binsertAdjacentHTML\s*\(|\bdocument\.write\s*\("
    )
    for filename in scripts:
        source = (ROOT / "static" / filename).read_text(encoding="utf-8")
        assert not forbidden.search(source), f"Unsafe HTML string sink found in {filename}"


def test_local_secrets_databases_backups_and_models_are_git_ignored() -> None:
    ignored = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
    required = {".env", ".env.*", "data/", "*.sqlite", "*.sqlite3", "*.db", "models/", "*.onnx"}
    assert required <= ignored


def test_core_dark_theme_text_tokens_meet_wcag_aa_contrast_against_panel() -> None:
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    root = css.split("}", 1)[0]
    tokens = dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", root))
    panel = tokens["panel"]
    for token in ("text", "muted", "accent", "danger"):
        ratio = _contrast_ratio(tokens[token], panel)
        assert ratio >= 4.5, f"--{token} contrast is {ratio:.2f}:1"
