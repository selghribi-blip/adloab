"""مُحدِّد خلفية التخزين (Storage Backend Selector).

الافتراضي: SQLite (ملف محلي، بلا سيرفر، مثالي للتشغيل الفردي وGitHub Actions).
للتبديل إلى Postgres ضع متغير البيئة:

    ADLOAB_DB_URL=postgresql://user:pass@host:5432/adloab

كل الوحدات تستورد هذا الملف:  from . import store as db
"""

from __future__ import annotations

import os
from typing import Any, Iterable

from . import db as _sqlite


def backend_name() -> str:
    url = os.getenv("ADLOAB_DB_URL", "").strip()
    if url.startswith(("postgres://", "postgresql://")):
        return "postgresql"
    return "sqlite"


def _impl():
    """تحميل خلفية Postgres بكسل (lazy) كي لا يكون psycopg متطلبًا إلزاميًا."""
    if backend_name() == "postgresql":
        from . import db_postgres

        return db_postgres
    return _sqlite


def init_db() -> None:
    _impl().init_db()


def upsert_target(target_id: str, name: str, url: str, interval_s: int, enabled: bool) -> None:
    _impl().upsert_target(target_id, name, url, interval_s, enabled)


def insert_check(target_id: str, result: dict[str, Any]) -> None:
    _impl().insert_check(target_id, result)


def recent_checks(target_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return _impl().recent_checks(target_id, limit)


def latest_checks(target_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    return _impl().latest_checks(list(target_ids))


def window_stats(target_id: str, hours: int = 24) -> dict[str, Any]:
    return _impl().window_stats(target_id, hours)


def open_incident(target_id: str, reason: str) -> None:
    _impl().open_incident(target_id, reason)


def resolve_incidents(target_id: str) -> None:
    _impl().resolve_incidents(target_id)


def incidents(limit: int = 50, only_open: bool = False) -> list[dict[str, Any]]:
    return _impl().incidents(limit, only_open)


def consecutive_failures(target_id: str) -> int:
    return _impl().consecutive_failures(target_id)


def alert_last_sent(target_id: str, kind: str) -> float | None:
    return _impl().alert_last_sent(target_id, kind)


def alert_mark_sent(target_id: str, kind: str, ts: float | None = None) -> None:
    _impl().alert_mark_sent(target_id, kind, ts)


def count_consecutive_slow(target_id: str, threshold_ms: float, limit: int = 10) -> int:
    return _impl().count_consecutive_slow(target_id, threshold_ms, limit)
