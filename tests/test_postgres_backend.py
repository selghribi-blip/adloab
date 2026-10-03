"""اختبارات خلفية Postgres — تعمل تلقائيًا بثلاث طرق:

1. إن كان المتغير TEST_DATABASE_URL مضبوطًا → تستخدمه.
2. وإلا وإن كانت حزمة pgserver مثبّتة → تُشغّل خادم Postgres حقيقيًا محليًا.
3. وإلا → تُتخطّى الاختبارات (skip) بدل أن تفشل.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="module")
def pg_dsn(tmp_path_factory) -> str:
    """إرجاع عنوان Postgres جاهز (من البيئة أو من خادم pgserver مؤقت)."""
    external = os.getenv("TEST_DATABASE_URL", "").strip()
    if external:
        return external

    pgserver = pytest.importorskip("pgserver", reason="pgserver غير مثبّت ولا يوجد TEST_DATABASE_URL")

    data_dir = tmp_path_factory.mktemp("pgdata")
    server = pgserver.get_server(str(data_dir))
    uri = server.get_uri()
    yield uri
    try:
        server.cleanup()
    except Exception:  # noqa: BLE001
        pass


@pytest.fixture()
def pg(pg_dsn: str, monkeypatch):
    monkeypatch.setenv("ADLOAB_DB_URL", pg_dsn)
    from app import db_postgres

    db_postgres.init_db()
    # تنظيف الجداول قبل كل اختبار
    with db_postgres.connect() as conn:
        conn.execute("TRUNCATE checks RESTART IDENTITY")
        conn.execute("TRUNCATE incidents RESTART IDENTITY")
        conn.execute("TRUNCATE targets")
    return db_postgres


def test_backend_roundtrip(pg):
    pg.upsert_target("pg1", "هدف تجريبي", "https://example.com", 60, True)

    now = time.time()
    for offset, ok, latency in [(30, True, 100.0), (20, True, 400.0), (10, True, 250.0)]:
        pg.insert_check(
            "pg1",
            {
                "ts": now - offset,
                "ok": ok,
                "status_code": 200,
                "total_ms": latency,
                "tls_days_left": 30,
            },
        )

    stats = pg.window_stats("pg1", hours=24)
    assert stats["checks"] == 3
    assert stats["uptime_pct"] == 100.0
    assert stats["max_ms"] == 400.0
    assert stats["tls_days_left"] == 30

    latest = pg.latest_checks(["pg1", "غير-موجود"])
    assert latest["pg1"]["total_ms"] == 250.0
    assert "غير-موجود" not in latest
    assert len(pg.recent_checks("pg1", limit=2)) == 2


def test_backend_failures_and_incidents(pg):
    pg.upsert_target("pg2", "هدف متوقف", "https://example.com", 60, True)
    pg.insert_check("pg2", {"ok": False, "reason": "انتهت المهلة"})
    pg.insert_check("pg2", {"ok": False, "reason": "انتهت المهلة"})
    assert pg.consecutive_failures("pg2") == 2

    pg.open_incident("pg2", "انتهت المهلة")
    pg.open_incident("pg2", "انتهت المهلة")
    assert len(pg.incidents(only_open=True)) == 1

    pg.resolve_incidents("pg2")
    assert pg.incidents(only_open=True) == []
    assert len(pg.incidents(limit=5)) == 1


def test_store_selector_picks_postgres(pg, monkeypatch):
    from app import store

    assert store.backend_name() == "postgresql"
    store.upsert_target("pg3", "عبر المحدِّد", "https://example.com", 120, True)
    store.insert_check("pg3", {"ok": True, "status_code": 200, "total_ms": 77.0})
    assert store.latest_checks(["pg3"])["pg3"]["total_ms"] == 77.0
    assert store.window_stats("pg3")["checks"] == 1
