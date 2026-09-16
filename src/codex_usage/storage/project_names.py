"""Local-only repository labels; never emitted as shared mapping events."""

from contextlib import closing
from collections.abc import Iterable
from pathlib import Path
import sqlite3
import unicodedata

from codex_usage.privacy.identifiers import project_id


def remember_project_names(
    database_path: str | Path, shared_key: bytes, canonical_remotes: Iterable[str],
) -> None:
    rows = []
    for remote in sorted(set(canonical_remotes)):
        if not remote or remote.startswith("prj_h1_") or "/" not in remote:
            continue
        label = remote.removeprefix("github.com/")
        label = "".join(c for c in label if not unicodedata.category(c).startswith("C"))
        rows.append((project_id(shared_key, remote), label))
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS local_project_names (
                project_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL
            )
        """)
        connection.executemany("""
            INSERT INTO local_project_names(project_id, display_name) VALUES (?, ?)
            ON CONFLICT(project_id) DO UPDATE SET display_name=excluded.display_name
        """, rows)


def load_local_project_names(connection: sqlite3.Connection) -> dict[str, str]:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_project_names'"
    ).fetchone()
    if not exists:
        return {}
    return dict(connection.execute("SELECT project_id, display_name FROM local_project_names"))
