"""اختبارات أساسية: حاجز الملكية + منطق النطاقات + إحصاءات التخزين."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.config import NotOwnedError, assert_allowed, domain_allowed  # noqa: E402


def test_domain_allowed_accepts_subdomain():
    owned = {"mysite.ma"}
    assert domain_allowed("mysite.ma", owned)
    assert domain_allowed("www.mysite.ma", owned)
    assert domain_allowed("api.staging.mysite.ma", owned)


def test_domain_allowed_rejects_lookalike():
    owned = {"mysite.ma"}
    # نطاق يستخدم نطاقك كبادئة نصية يجب ألا يُقبل
    assert not domain_allowed("mysite.ma.evil.com", owned)
    assert not domain_allowed("notmysite.ma", owned)
    assert not domain_allowed("google.com", owned)


def test_assert_allowed_raises_for_foreign_domain():
    with pytest.raises(NotOwnedError):
        assert_allowed("https://some-random-site.com", owned={"example.com"})


def test_assert_allowed_passes_for_owned():
    assert assert_allowed("https://example.com", owned={"example.com"}) == "example.com"


def test_db_roundtrip_and_stats(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    db.init_db()
    db.upsert_target("t1", "تجربة", "https://example.com", 60, True)

    now = time.time()
    for offset, ok, latency in [(30, True, 120.0), (20, True, 300.0), (10, True, 200.0)]:
        db.insert_check(
            "t1",
            {"ts": now - offset, "ok": ok, "status_code": 200, "total_ms": latency, "tls_days_left": 42},
        )

    stats = db.window_stats("t1", hours=24)
    assert stats["checks"] == 3
    assert stats["uptime_pct"] == 100.0
    assert stats["max_ms"] == 300.0
    assert stats["tls_days_left"] == 42

    # أحدث فحص هو (now - 10) بزمن 200ms
    assert db.latest_checks(["t1"])["t1"]["total_ms"] == 200.0
    assert len(db.recent_checks("t1", limit=10)) == 3


def test_incident_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    db.init_db()
    db.upsert_target("t2", "تجربة", "https://example.com", 60, True)

    db.insert_check("t2", {"ok": False, "reason": "انتهت المهلة"})
    db.insert_check("t2", {"ok": False, "reason": "انتهت المهلة"})
    assert db.consecutive_failures("t2") == 2

    db.open_incident("t2", "انتهت المهلة")
    db.open_incident("t2", "انتهت المهلة")  # لا تُفتح حادثة مكرّرة
    assert len(db.incidents(only_open=True)) == 1

    db.resolve_incidents("t2")
    assert db.incidents(only_open=True) == []
    assert len(db.incidents(limit=10)) == 1
