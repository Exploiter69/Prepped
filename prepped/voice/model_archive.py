"""Bounded, path-safe extraction for explicitly downloaded voice model archives."""
from __future__ import annotations

import argparse
import stat
import zipfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE_ENTRIES = 20_000
MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024


def extract_model_archive(archive_path: Path, destination: Path) -> None:
    """Validate every ZIP member before extracting any content."""
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("Voice model archive contains too many entries.")
        total_size = 0

        for member in members:
            name = member.filename
            relative = PurePosixPath(name)
            if (
                not name
                or "\\" in name
                or "\\" in name
                or relative.is_absolute()
                or any(part in {"", ".", ".."} for part in relative.parts)
                or (relative.parts and ":" in relative.parts[0])
            ):
                raise ValueError("Voice model archive contains an unsafe path.")

            target = (root / Path(*relative.parts)).resolve()
            if target != root and root not in target.parents:
                raise ValueError("Voice model archive attempts to write outside the models directory.")

            file_type = (member.external_attr >> 16) & 0o170000
            if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError("Voice model archive contains a link or special file.")
            if member.file_size < 0:
                raise ValueError("Voice model archive contains an invalid file size.")
            total_size += member.file_size
            if total_size > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("Voice model archive exceeds the extraction size limit.")

        archive.extractall(root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely extract a downloaded Prepped voice model ZIP.")
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    extract_model_archive(args.archive, args.destination)


if __name__ == "__main__":
    main()
