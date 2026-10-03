"""خلفية Postgres: نفس واجهة app.db لكن على خادم Postgres حقيقي.

مفيدة عندما:
  - تعمل اللوحة على أكثر من نسخة (فلا تتصارع النسخ على ملف SQLite واحد)،
  - تريد تاريخًا طويلًا للفحوصات،
  - تستخدم خطة استضافة مجانية تعطيك قاعدة Postgres (مثل Render/Railway/Neon أو
    ardo/أرصدة DigitalOcean من GitHub Student Pack).

التبديل: ضع ADLOAB_DB_URL=postgresql://user:pass@host:5432/dbname وسيُستخدم تلقائيًا.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row

from .stats import window_stats_from_rows

DSN = os.getenv("ADLOAB_DB_URL", "")

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    url          TEXT NOT NULL,
    interval_s   INTEGER NOT NULL DEFAULT 300,
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at   DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS checks (
    id            BIGSERIAL PRIMARY KEY,
    target_id     TEXT NOT NULL,
    ts            DOUBLE PRECISION NOT NULL,
    ok            BOOLEAN NOT NULL,
    status_code   INTEGER,
    reason        TEXT,
    dns_ms        DOUBLE PRECISION,
    connect_ms    DOUBLE PRECISION,
    ttfb_ms       DOUBLE PRECISION,
    total_ms      DOUBLE PRECISION,
    tls_days_left DOUBLE PRECISION,
    browser_ms    DOUBLE PRECISION,
    browser_note  TEXT
);
CREATE INDEX IF NOT EXISTS idx_checks_target_ts ON checks(target_id, ts DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id          BIGSERIAL PRIMARY KEY,
    target_id   TEXT NOT NULL,
    started_at  DOUBLE PRECISION NOT NULL,
    resolved_at DOUBLE PRECISION,
    reason      TEXT
);
CREATE INDEX IF NOT EXISTS idx_incidents_open ON incidents(target_id, resolved_at);

CREATE TABLE IF NOT EXISTS alert_state (
    target_id    TEXT NOT NULL,
    kind         TEXT NOT NULL,
    last_sent_at DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (target_id, kind)
);
"""


def _dsn() -> str:
    dsn = os.getenv("ADLOAB_DB_URL", DSN)
    if not dsn:
        raise RuntimeError("ADLOAB_DB_URL غير مضبوط — لا يمكن استخدام خلفية Postgres.")
    return dsn


def connect() -> psycopg.Connection:
    """اتصال واحد لكل عملية (autocommit) — بسيط وآمن مع أحجام فحوصاتنا."""
    return psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row, connect_timeout=10)


def _rows(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with _lock, connect() as conn:
        return list(conn.execute(query, params).fetchall())


def init_db() -> None:
    with _lock, connect() as conn:
        conn.execute(SCHEMA)


def upsert_target(target_id: str, name: str, url: str, interval_s: int, enabled: bool) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """INSERT INTO targets (id, name, url, interval_s, enabled, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT(id) DO UPDATE SET
                 name=EXCLUDED.name, url=EXCLUDED.url,
                 interval_s=EXCLUDED.interval_s, enabled=EXCLUDED.enabled,
                 updated_at=EXCLUDED.updated_at""",
            (target_id, name, url, interval_s, bool(enabled), time.time()),
        )


def insert_check(target_id: str, result: dict[str, Any]) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """INSERT INTO checks
               (target_id, ts, ok, status_code, reason, dns_ms, connect_ms, ttfb_ms,
                total_ms, tls_days_left, browser_ms, browser_note)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                target_id,
                result.get("ts", time.time()),
                bool(result.get("ok")),
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
    return _rows(
        "SELECT * FROM checks WHERE target_id=%s ORDER BY ts DESC LIMIT %s", (target_id, limit)
    )


def latest_checks(target_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    target_ids = list(target_ids)
    if not target_ids:
        return {}
    rows = _rows(
        """SELECT DISTINCT ON (target_id) * FROM checks
           WHERE target_id = ANY(%s) ORDER BY target_id, ts DESC""",
        (target_ids,),
    )
    return {row["target_id"]: row for row in rows}


def window_stats(target_id: str, hours: int = 24) -> dict[str, Any]:
    since = time.time() - hours * 3600
    rows = _rows(
        "SELECT ok, total_ms, ttfb_ms, tls_days_left FROM checks WHERE target_id=%s AND ts>=%s",
        (target_id, since),
    )
    return window_stats_from_rows(rows, hours)


def open_incident(target_id: str, reason: str) -> None:
    with _lock, connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM incidents WHERE target_id=%s AND resolved_at IS NULL LIMIT 1", (target_id,)
        ).fetchone()
        if exists:
            return
        conn.execute(
            "INSERT INTO incidents (target_id, started_at, reason) VALUES (%s,%s,%s)",
            (target_id, time.time(), reason[:500]),
        )


def resolve_incidents(target_id: str) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "UPDATE incidents SET resolved_at=%s WHERE target_id=%s AND resolved_at IS NULL",
            (time.time(), target_id),
        )


def incidents(limit: int = 50, only_open: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM incidents"
    if only_open:
        query += " WHERE resolved_at IS NULL"
    query += " ORDER BY started_at DESC LIMIT %s"
    return _rows(query, (limit,))


def consecutive_failures(target_id: str) -> int:
    rows = _rows(
        "SELECT ok FROM checks WHERE target_id=%s ORDER BY ts DESC LIMIT 20", (target_id,)
    )
    count = 0
    for row in rows:
        if row["ok"]:
            break
        count += 1
    return count


# ------------------------- حالة التنبيهات (تهدئة) ------------------------- #

def alert_last_sent(target_id: str, kind: str) -> float | None:
    rows = _rows(
        "SELECT last_sent_at FROM alert_state WHERE target_id=%s AND kind=%s",
        (target_id, kind),
    )
    return float(rows[0]["last_sent_at"]) if rows else None


def alert_mark_sent(target_id: str, kind: str, ts: float | None = None) -> None:
    with _lock, connect() as conn:
        conn.execute(
            """INSERT INTO alert_state (target_id, kind, last_sent_at) VALUES (%s,%s,%s)
               ON CONFLICT (target_id, kind) DO UPDATE SET last_sent_at=EXCLUDED.last_sent_at""",
            (target_id, kind, ts or time.time()),
        )


def count_consecutive_slow(target_id: str, threshold_ms: float, limit: int = 10) -> int:
    """كم فحصًا متتاليًا تجاوز حد البطء (من الأحدث للخلف)."""
    rows = _rows(
        "SELECT ok, total_ms FROM checks WHERE target_id=%s ORDER BY ts DESC LIMIT %s",
        (target_id, limit),
    )
    count = 0
    for row in rows:
        if not row["ok"] or row["total_ms"] is None or float(row["total_ms"]) < threshold_ms:
            break
        count += 1
    return count
