from __future__ import annotations

import os
import sqlite3
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
        assert connection.execute("PRAGMA trusted_schema").fetchone()[0] == 0


def test_unusable_database_parent_fails_without_touching_unrelated_file(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("keep", encoding="utf-8")
    with pytest.raises(OSError):
        initialize_database(blocker / "prepped.sqlite3")
    assert blocker.read_text(encoding="utf-8") == "keep"


def test_schema_three_database_upgrade_is_additive_and_idempotent(tmp_path: Path) -> None:
    from prepped.career import initialize_career_database
    from prepped.intelligence import initialize_intelligence_database
    from prepped.progress import initialize_progress_database

    database = tmp_path / "upgrade.sqlite3"
    initialize_database(database)
    initialize_career_database(database)
    initialize_progress_database(database)
    initialize_intelligence_database(database)
    with connect_database(database) as connection:
        connection.execute(
            "INSERT INTO sessions (id, scenario_id, scenario_version, status, created_at) "
            "VALUES ('preserved-session', 'project-explanation', '1.0.0', 'in_progress', '2026-01-01T00:00:00+00:00')"
        )
        connection.execute(
            "INSERT INTO answers (id, session_id, question_id, answer_text, position, created_at) "
            "VALUES ('preserved-answer', 'preserved-session', 'q1', 'keep this answer', 0, '2026-01-01T00:00:00+00:00')"
        )
        connection.execute("DROP TABLE adaptive_plan_items")
        connection.execute("DROP TABLE adaptive_plans")
        connection.execute("PRAGMA user_version = 3")

    from prepped.ai_provider import initialize_ai_database
    from prepped.career_prep import initialize_career_prep_database
    from prepped.preferences import initialize_preferences_database

    initialize_database(database)
    initialize_career_database(database)
    initialize_progress_database(database)
    initialize_intelligence_database(database)
    initialize_preferences_database(database)
    initialize_career_prep_database(database)
    initialize_ai_database(database)
    with connect_database(database) as ver_conn:
        ver_conn.execute("PRAGMA user_version = 5")
    initialize_database(database)

    with connect_database(database) as connection:
        assert connection.execute("SELECT answer_text FROM answers WHERE id='preserved-answer'").fetchone()[0] == "keep this answer"
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 5
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='learner_preferences'").fetchone()
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='learner_projects'").fetchone()
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='mock_interviews'").fetchone()
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='ai_settings'").fetchone()
        assert connection.execute("SELECT name FROM sqlite_master WHERE name='adaptive_plans'").fetchone()
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="Requires an unprivileged POSIX user")
def test_read_only_custom_database_directory_fails_cleanly(tmp_path: Path) -> None:
    directory = tmp_path / "read-only-store"
    directory.mkdir()
    os.chmod(directory, 0o500)
    database = directory / "prepped.sqlite3"
    try:
        with pytest.raises(PermissionError):
            initialize_database(database)
        assert not database.exists()
    finally:
        os.chmod(directory, 0o700)


def test_simulated_sqlite_disk_full_rolls_back_and_preserves_integrity(tmp_path: Path) -> None:
    database = tmp_path / "disk-full.sqlite3"
    initialize_database(database)
    with connect_database(database) as connection:
        connection.execute("CREATE TABLE disk_probe (payload BLOB NOT NULL)")
    with pytest.raises(sqlite3.OperationalError, match="full"):
        with connect_database(database) as connection:
            pages = connection.execute("PRAGMA page_count").fetchone()[0]
            connection.execute(f"PRAGMA max_page_count = {pages}")
            connection.execute(
                "INSERT INTO disk_probe(payload) VALUES (?)",
                (b"x" * (4 * 1024 * 1024),),
            )
    with connect_database(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM disk_probe").fetchone()[0] == 0
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
