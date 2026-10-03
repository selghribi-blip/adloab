"""طبقة التخزين: SQLite (ملف واحد، بلا سيرفر، مجاني بالكامل)."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable

from .config import DATA_DIR

DB_PATH = Path(DATA_DIR) / "uptime.sqlite3"

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    url          TEXT NOT NULL,
    interval_s   INTEGER NOT NULL DEFAULT 300,
    enabled      INTEGER NOT NULL DEFAULT 1,
    updated_at   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS checks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id     TEXT NOT NULL,
    ts            REAL NOT NULL,
    ok            INTEGER NOT NULL,
    status_code   INTEGER,
    reason        TEXT,
    dns_ms        REAL,
    connect_ms    REAL,
    ttfb_ms       REAL,
    total_ms      REAL,
    tls_days_left REAL,
    browser_ms    REAL,
    browser_note  TEXT
);
CREATE INDEX IF NOT EXISTS idx_checks_target_ts ON checks(target_id, ts DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id   TEXT NOT NULL,
    started_at  REAL NOT NULL,
    resolved_at REAL,
    reason      TEXT
);
CREATE INDEX IF NOT EXISTS idx_incidents_open ON incidents(target_id, resolved_at);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    with _lock, connect() as conn:
        conn.executescript(SCHEMA)


def upsert_target(target_id: str, name: str, url: str, interval_s: int, enabled: bool) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """INSERT INTO targets (id, name, url, interval_s, enabled, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, url=excluded.url,
                 interval_s=excluded.interval_s, enabled=excluded.enabled,
                 updated_at=excluded.updated_at""",
            (target_id, name, url, interval_s, int(enabled), time.time()),
        )


def insert_check(target_id: str, result: dict[str, Any]) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """INSERT INTO checks
               (target_id, ts, ok, status_code, reason, dns_ms, connect_ms, ttfb_ms,
                total_ms, tls_days_left, browser_ms, browser_note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                target_id,
                result.get("ts", time.time()),
                int(bool(result.get("ok"))),
                result.get("status_code"),
                result.get("reason"),
                result.get("dns_ms"),
                result.get("connect_ms"),
                result.get("ttfb_ms"),
                result.get("total_ms"),
                result.get("tls_days_left"),
                result.get("browser_ms"),
                result.get("browser_note"),
            ),
        )


def recent_checks(target_id: str, limit: int = 100) -> list[dict[str, Any]]:
    with _lock, connect() as conn:
        rows = conn.execute(
            "SELECT * FROM checks WHERE target_id=? ORDER BY ts DESC LIMIT ?",
            (target_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def latest_checks(target_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with _lock, connect() as conn:
        for tid in target_ids:
            row = conn.execute(
                "SELECT * FROM checks WHERE target_id=? ORDER BY ts DESC LIMIT 1", (tid,)
            ).fetchone()
            if row:
                out[tid] = dict(row)
    return out


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return round(ordered[index], 1)


def window_stats(target_id: str, hours: int = 24) -> dict[str, Any]:
    """إحصاءات النافذة الزمنية: نسبة التشغيل، متوسط/وسيط/ذروة زمن الاستجابة."""
    since = time.time() - hours * 3600
    with _lock, connect() as conn:
        rows = conn.execute(
            "SELECT ok, total_ms, ttfb_ms, tls_days_left FROM checks WHERE target_id=? AND ts>=?",
            (target_id, since),
        ).fetchall()

    total = len(rows)
    ok_rows = [r for r in rows if r["ok"]]
    latencies = [r["total_ms"] for r in ok_rows if r["total_ms"] is not None]
    tls_values = [r["tls_days_left"] for r in ok_rows if r["tls_days_left"] is not None]

    return {
        "checks": total,
        "uptime_pct": round(100 * len(ok_rows) / total, 2) if total else None,
        "avg_ms": _percentile(latencies, 50),
        "p95_ms": _percentile(latencies, 95),
        "max_ms": round(max(latencies), 1) if latencies else None,
        "tls_days_left": min(tls_values) if tls_values else None,
        "window_hours": hours,
    }


def open_incident(target_id: str, reason: str) -> None:
    with _lock, connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM incidents WHERE target_id=? AND resolved_at IS NULL", (target_id,)
        ).fetchone()
        if exists:
            return
        conn.execute(
            "INSERT INTO incidents (target_id, started_at, reason) VALUES (?,?,?)",
            (target_id, time.time(), reason[:500]),
        )


def resolve_incidents(target_id: str) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "UPDATE incidents SET resolved_at=? WHERE target_id=? AND resolved_at IS NULL",
            (time.time(), target_id),
        )


def incidents(limit: int = 50, only_open: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM incidents"
    params: list[Any] = []
    if only_open:
        query += " WHERE resolved_at IS NULL"
    query += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    with _lock, connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def consecutive_failures(target_id: str) -> int:
    with _lock, connect() as conn:
        rows = conn.execute(
            "SELECT ok FROM checks WHERE target_id=? ORDER BY ts DESC LIMIT 20", (target_id,)
        ).fetchall()
    count = 0
    for row in rows:
        if row["ok"]:
            break
        count += 1
    return count
