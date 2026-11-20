from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from prepped.database import connect_database, initialize_database


@pytest.mark.skipif(os.name != "posix", reason="POSIX file-mode assertions")
def test_database_file_and_new_data_directory_are_private(tmp_path: Path) -> None:
    database = tmp_path / "data" / "prepped.sqlite3"
    initialize_database(database)
    assert stat.S_IMODE(database.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(database.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="POSIX file-mode assertions")
def test_existing_database_permissions_are_restricted(tmp_path: Path) -> None:
    database = tmp_path / "prepped.sqlite3"
    database.touch(mode=0o644)
    os.chmod(database, 0o644)
    initialize_database(database)
    assert stat.S_IMODE(database.stat().st_mode) == 0o600


def test_database_symlink_target_is_rejected(tmp_path: Path) -> None:
    real_database = tmp_path / "real.sqlite3"
    initialize_database(real_database)
    link = tmp_path / "linked.sqlite3"
    link.symlink_to(real_database)
    with pytest.raises(OSError, match="symlink"):
        initialize_database(link)


def test_transaction_rolls_back_on_process_level_exception_and_database_remains_valid(tmp_path: Path) -> None:
    database = tmp_path / "rollback.sqlite3"
    initialize_database(database)
    with connect_database(database) as connection:
        connection.execute("CREATE TABLE rollback_probe (value TEXT NOT NULL)")
    with pytest.raises(KeyboardInterrupt):
        with connect_database(database) as connection:
            connection.execute("INSERT INTO rollback_probe(value) VALUES ('must roll back')")
            raise KeyboardInterrupt()
    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM rollback_probe").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_unusable_database_parent_fails_without_touching_unrelated_file(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("keep", encoding="utf-8")
    with pytest.raises(OSError):
        initialize_database(blocker / "prepped.sqlite3")
    assert blocker.read_text(encoding="utf-8") == "keep"
