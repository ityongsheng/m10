from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlparse

from .config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    valid_count INTEGER NOT NULL,
    invalid_count INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    synthetic_demo INTEGER NOT NULL DEFAULT 0,
    source_sha256 TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS processing_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id),
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    params_json TEXT NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0,
    anomaly_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES processing_runs(id),
    timestamp TEXT NOT NULL,
    station_id TEXT NOT NULL,
    irradiance_w_m2 REAL NOT NULL,
    ambient_temp_c REAL NOT NULL,
    module_temp_c REAL NOT NULL,
    power_kw REAL NOT NULL,
    efficiency_proxy REAL NOT NULL,
    cluster_id INTEGER,
    anomaly_score REAL,
    is_anomaly INTEGER NOT NULL DEFAULT 0,
    known_issue_label INTEGER
);
CREATE INDEX IF NOT EXISTS idx_records_run_time ON records(run_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_records_run_anomaly ON records(run_id, is_anomaly);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES processing_runs(id),
    record_id INTEGER NOT NULL REFERENCES records(id),
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


def _sqlite_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise RuntimeError(
            "当前便携模式仅支持 SQLite；集群模式请使用 M10_DATABASE_URL 配置 MySQL 适配层"
        )
    path = Path(settings.database_url[len(prefix) :])
    if not path.is_absolute():
        path = (settings.data_root / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _is_mysql() -> bool:
    return settings.database_url.startswith(("mysql://", "mysql+pymysql://"))


class _MySQLConnection:
    def __init__(self, raw: Any):
        self.raw = raw

    def execute(self, sql: str, params: tuple | list = ()) -> Any:
        cursor = self.raw.cursor()
        cursor.execute(sql.replace("?", "%s"), params)
        return cursor

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                try:
                    self.execute(statement)
                except Exception as exc:
                    # MySQL has no portable CREATE INDEX IF NOT EXISTS. A
                    # duplicate index on restart is harmless for this local
                    # development database.
                    if "duplicate" not in str(exc).lower() and "already exists" not in str(exc).lower():
                        raise

    def __enter__(self) -> "_MySQLConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if exc_type:
                self.raw.rollback()
            else:
                self.raw.commit()
        finally:
            self.raw.close()


def _mysql_connection() -> _MySQLConnection:
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("MySQL 模式需要安装 pymysql") from exc
    parsed = urlparse(settings.database_url.replace("mysql+pymysql://", "mysql://", 1))
    if not parsed.hostname or not parsed.path.strip("/"):
        raise RuntimeError("MySQL URL 缺少主机或数据库名")
    raw = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=parsed.path.strip("/"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    return _MySQLConnection(raw)


@contextmanager
def connection() -> Iterator[Any]:
    if _is_mysql():
        with _mysql_connection() as conn:
            yield conn
        return
    conn = sqlite3.connect(_sqlite_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        if _is_mysql():
            mysql_schema = (
                SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGINT PRIMARY KEY AUTO_INCREMENT")
                .replace("TEXT NOT NULL DEFAULT '{}'", "LONGTEXT NOT NULL")
                # MySQL requires a key length for TEXT columns; these fields
                # participate in the records indexes, so use bounded strings.
                .replace("timestamp TEXT NOT NULL", "timestamp VARCHAR(64) NOT NULL")
                .replace("station_id TEXT NOT NULL", "station_id VARCHAR(128) NOT NULL")
                .replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX")
            )
            conn.executescript(mysql_schema)
            # Upgrade databases created by an earlier build that left indexed
            # text columns as TEXT. This keeps a persistent local MySQL volume
            # restartable after the schema adapter is upgraded.
            conn.execute("ALTER TABLE records MODIFY timestamp VARCHAR(64) NOT NULL")
            conn.execute("ALTER TABLE records MODIFY station_id VARCHAR(128) NOT NULL")
        else:
            conn.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)

