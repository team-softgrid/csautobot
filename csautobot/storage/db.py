"""SQLite 커넥션 관리 + 스키마 초기화."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = HERE / "csautobot.db"
SCHEMA_PATH = HERE / "schema.sql"


def get_db_path() -> Path:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path), isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """스키마가 없으면 생성. 여러 번 호출해도 안전 (IF NOT EXISTS)."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with _connect(db_path) as conn:
        conn.executescript(schema)


@contextmanager
def get_conn(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """컨텍스트 매니저: 최초 호출 시 스키마 자동 생성."""
    path = db_path or get_db_path()
    if not path.exists():
        init_db(path)
    conn = _connect(path)
    try:
        yield conn
    finally:
        conn.close()
