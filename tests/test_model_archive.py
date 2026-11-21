from __future__ import annotations

import stat
import zipfile
from pathlib import Path

import pytest

from prepped.voice.model_archive import extract_model_archive


def test_extract_model_archive_accepts_normal_model_layout(tmp_path: Path) -> None:
    archive_path = tmp_path / "model.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("vosk-model/conf/model.conf", "model")
        archive.writestr("vosk-model/am/final.mdl", "weights")

    destination = tmp_path / "models"
    extract_model_archive(archive_path, destination)

    assert (destination / "vosk-model/conf/model.conf").read_text() == "model"
    assert (destination / "vosk-model/am/final.mdl").read_text() == "weights"


@pytest.mark.parametrize(
    "member_name",
    ["../outside.txt", "/tmp/outside.txt", "C:/outside.txt", r"folder\..\outside.txt"],
)
def test_extract_model_archive_rejects_unsafe_paths_before_writing(
    tmp_path: Path, member_name: str
) -> None:
    archive_path = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(member_name, "must not escape")

    destination = tmp_path / "models"
    with pytest.raises(ValueError, match="unsafe path"):
        extract_model_archive(archive_path, destination)

    assert not (tmp_path / "outside.txt").exists()


def test_extract_model_archive_rejects_symlink_entries(tmp_path: Path) -> None:
    archive_path = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("model/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(info, "../outside")

    with pytest.raises(ValueError, match="link or special"):
        extract_model_archive(archive_path, tmp_path / "models")


def test_extract_model_archive_enforces_expanded_size_limit(tmp_path: Path, monkeypatch) -> None:
    import prepped.voice.model_archive as module

    archive_path = tmp_path / "large.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("model/weights", b"x" * 16)
    monkeypatch.setattr(module, "MAX_UNCOMPRESSED_BYTES", 10)

    with pytest.raises(ValueError, match="size limit"):
        extract_model_archive(archive_path, tmp_path / "models")


def test_voice_setup_calls_the_validated_extractor() -> None:
    root = Path(__file__).resolve().parents[1]
    setup_script = (root / "scripts" / "setup_voice.sh").read_text(encoding="utf-8")

    assert "-m prepped.voice.model_archive" in setup_script
    assert "zf.extractall" not in setup_script
