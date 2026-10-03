"""اختبارات قناة تنبيهات Telegram.

لا نتصل بـ Telegram الحقيقي: نستخدم httpx.MockTransport للتأكد من أن الطلب
المُرسل مطابق تمامًا لمتطلبات Bot API (الرابط، chat_id، parse_mode، التهريب HTML).
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.alerts import (  # noqa: E402
    KIND_DOWN,
    KIND_SLOW,
    KIND_TEST,
    KIND_TLS,
    KIND_UP,
    AlertSettings,
    alert_status,
    build_alert_text,
    evaluate_kinds,
    notify,
    send_telegram,
)
from app.config import Target  # noqa: E402

TOKEN = "123456:TEST-TOKEN-abcd"
CHAT = "-1001234567890"


def run_sync(coro):
    """تشغيل كوروتين في خيط منفصل.

    السبب: اختبارات E2E (Playwright المتزامن) قد تعمل في نفس الخيط وتترك حلقة

    أحداث نشطة، فيرفض asyncio.run العمل في خيط فيه حلقة قائمة. الخيط الجديد
    يضمن بيئة asyncio نظيفة دائمًا، مع تشغيل الكوروتين فعليًا في حلقة حقيقية.
    """
    outcome: dict = {}

    def worker() -> None:
        try:
            outcome["value"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001
            outcome["error"] = exc

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "alerts.sqlite3")
    db.init_db()
    return db


@pytest.fixture()
def target() -> Target:
    return Target(id="t1-example-com", name="مدونتي", url="https://example.com")


def settings(**overrides) -> AlertSettings:
    base = dict(
        enabled=True,
        telegram_bot_token=TOKEN,
        telegram_chat_id=CHAT,
        latency_alert_ms=0,
        latency_consecutive=3,
        tls_warn_days=7,
        cooldown_seconds={"down": 0, "up": 0, "slow": 1800, "tls": 86400},
    )
    base.update(overrides)
    return AlertSettings(**base)


def capturing_transport(calls: list[httpx.Request], status: int = 200):
    """خادم وهمي يسجّل الطلبات ويعيد ردًّا ناجحًا كالذي يعيده Telegram."""

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if status == 429:
            return httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 0}})
        if status != 200:
            return httpx.Response(status, json={"ok": False, "description": "Unauthorized"})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    return httpx.MockTransport(handler)


def test_request_shape_matches_telegram_api(isolated_db):
    """شكل الطلب: الرابط يحتوي التوكن ودالة sendMessage، والحقول مطابقة للمواصفة."""
    calls: list[httpx.Request] = []
    sent = run_sync(
        send_telegram("<b>مرحبًا</b>", settings(), transport=capturing_transport(calls))
    )

    assert sent is True
    assert len(calls) == 1
    request = calls[0]
    assert request.method == "POST"
    assert request.url.path == f"/bot{TOKEN}/sendMessage"
    assert request.headers["content-type"].startswith("application/json")

    body = json.loads(request.content)
    assert body["chat_id"] == CHAT
    assert body["text"] == "<b>مرحبًا</b>"
    assert body["parse_mode"] == "HTML"
    assert body["disable_web_page_preview"] is True
    assert body["disable_notification"] is False


def test_topic_and_silent_options(isolated_db):
    """المواضيع (message_thread_id) والتنبيه الصامت يعملان عند ضبطهما."""
    calls: list[httpx.Request] = []
    cfg = settings(telegram_topic_id="42", telegram_disable_notification=True)
    run_sync(send_telegram("نص", cfg, transport=capturing_transport(calls)))
    body = json.loads(calls[0].content)
    assert body["message_thread_id"] == "42"
    assert body["disable_notification"] is True


def test_retry_on_rate_limit(isolated_db):
    """عند 429 يُعاد المحاولة ثم ينجح الإرسال (بلا نوم طويل في الاختبار)."""
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 0}})
        return httpx.Response(200, json={"ok": True})

    sent = run_sync(send_telegram("نص", settings(), transport=httpx.MockTransport(handler)))
    assert sent is True
    assert len(calls) == 2  # المحاولة الأولى + إعادة المحاولة


def test_invalid_token_does_not_retry(isolated_db):
    """401/404 (توكن أو رقم محادثة خاطئ) لا تُهدر محاولات: تفشل فورًا."""
    calls: list[httpx.Request] = []
    sent = run_sync(
        send_telegram(
            "نص",
            settings(),
            transport=capturing_transport(calls, status=401),
            retry_wait=0,
        )
    )
    assert sent is False
    assert len(calls) == 1


def test_not_configured_skips(isolated_db):
    """بلا توكن/محادثة لا يُرسل شيء ولا يتعطّل شيء."""
    calls: list[httpx.Request] = []
    cfg = settings(telegram_bot_token="", telegram_chat_id="")
    assert run_sync(send_telegram("نص", cfg, transport=capturing_transport(calls))) is False
    assert calls == []


# ---------------------------- محتوى الرسالة ---------------------------- #

def test_message_escapes_html(target):
    """النصوص القادمة من الموقع تُهرَّب حتى لا تُفسد رسالة HTML."""
    result = {"ok": False, "reason": 'استجابة <script>alert("x")</script> & غير ذلك', "ts": 1.0}
    text = build_alert_text(target, result, KIND_DOWN)
    assert "&lt;script&gt;" in text
    assert "&amp;" in text
    assert "<script>" not in text
    assert "🔴 توقف الموقع" in text
    assert "مدونتي" in text


def test_message_contents_for_each_kind(target):
    down = {"ok": False, "status_code": 500, "reason": "خطأ سيرفر", "total_ms": 1200.5, "ts": 1.0}
    text = build_alert_text(target, down, KIND_DOWN)
    assert "500" in text and "خطأ سيرفر" in text and "1200 ms" in text

    tls = {"ok": True, "tls_days_left": 3.4, "ts": 1.0}
    text = build_alert_text(target, tls, KIND_TLS)
    assert "🔐" in text and "3" in text

    slow = {"ok": True, "total_ms": 3000, "ts": 1.0}
    text = build_alert_text(target, slow, KIND_SLOW)
    assert "🐢" in text and "3000 ms" in text

    test_msg = build_alert_text(None, {}, KIND_TEST)
    assert "🧪" in test_msg and "تعمل بنجاح" in test_msg


# ------------------------- قرارات التنبيه والتهدئة ------------------------- #

def test_evaluate_kinds_rules(target):
    cfg = settings(latency_alert_ms=1000)

    assert evaluate_kinds({"ok": False, "reason": "انتهت المهلة"}, cfg) == [KIND_DOWN]
    assert evaluate_kinds({"ok": True, "total_ms": 100}, cfg) == []
    assert evaluate_kinds({"ok": True, "total_ms": 1500}, cfg) == [KIND_SLOW]
    assert evaluate_kinds({"ok": True, "total_ms": 100}, cfg, recovered=True) == [KIND_UP]

    # الشهادة تُنبّه حتى مع أداء سليم
    assert KIND_TLS in evaluate_kinds({"ok": True, "tls_days_left": 2, "total_ms": 100}, cfg)
    assert KIND_TLS not in evaluate_kinds({"ok": True, "tls_days_left": 60, "total_ms": 100}, cfg)

    # تعطيل حد البطء أو حد الشهادة
    assert evaluate_kinds({"ok": True, "total_ms": 99999}, settings(latency_alert_ms=0)) == []
    assert evaluate_kinds({"ok": True, "tls_days_left": 1}, settings(tls_warn_days=0)) == []


def test_cooldown_blocks_then_force_sends(isolated_db, target):
    """البطء: يُرسل مرة ثم يُحجب فترة التهدئة، والتنبيه القسري يتجاوزها."""
    calls: list[httpx.Request] = []
    cfg = settings(latency_alert_ms=1000)
    transport = capturing_transport(calls)
    result = {"ok": True, "total_ms": 5000, "ts": time.time()}

    first = run_sync(notify(target, result, KIND_SLOW, cfg, transport=transport, retry_wait=0))
    second = run_sync(notify(target, result, KIND_SLOW, cfg, transport=transport, retry_wait=0))
    forced = run_sync(
        notify(target, result, KIND_SLOW, cfg, force=True, transport=transport, retry_wait=0)
    )

    assert (first, second, forced) == (True, False, True)
    assert len(calls) == 2  # الثانية حُجبت بالتهدئة
    assert isolated_db.alert_last_sent(target.id, KIND_SLOW) is not None


def test_cooldown_zero_always_sends(isolated_db, target):
    """تنبيه التوقف فوري في كل مرة (تهدئة = 0) — الحماية من التكرار في إدارة الحوادث."""
    calls: list[httpx.Request] = []
    cfg = settings()
    transport = capturing_transport(calls)
    result = {"ok": False, "reason": "انتهت المهلة", "ts": time.time()}

    for _ in range(2):
        assert run_sync(
            notify(target, result, KIND_DOWN, cfg, transport=transport, retry_wait=0)
        )
    assert len(calls) == 2


def test_disabled_master_switch(isolated_db, target):
    """المفتاح العام: enabled=false يمنع كل شيء ما لم يكن force."""
    calls: list[httpx.Request] = []
    cfg = settings(enabled=False)
    transport = capturing_transport(calls)
    blocked = run_sync(
        notify(target, {"ok": False, "reason": "x"}, KIND_DOWN, cfg, transport=transport)
    )
    forced = run_sync(
        notify(target, {"ok": False, "reason": "x"}, KIND_DOWN, cfg, force=True,
               transport=transport, retry_wait=0)
    )
    assert blocked is False and forced is True and len(calls) == 1


def test_consecutive_slow_counter(isolated_db, target):
    """عدّاد البطء المتتالي: يستخدمه المجدول لتفادي التنبيه على ارتفاع عابر."""
    for latency in (3000, 2500, 200, 3000):
        isolated_db.insert_check(
            target.id, {"ok": True, "total_ms": latency, "ts": time.time()}
        )
    assert isolated_db.count_consecutive_slow(target.id, 1000) == 1
    isolated_db.insert_check(target.id, {"ok": True, "total_ms": 4000})
    isolated_db.insert_check(target.id, {"ok": True, "total_ms": 5000})
    assert isolated_db.count_consecutive_slow(target.id, 1000) == 3


def test_alert_status_masks_token(isolated_db):
    """حالة القناة تعرض آخر 4 أحرف فقط — لا تكشف التوكن في الواجهة أو السجلات."""
    status = alert_status(settings())
    assert status["channels"].startswith("Telegram ✅")
    assert TOKEN not in status["channels"]
    assert "abcd" in status["channels"]

    partial = alert_status(settings(telegram_chat_id=""))
    assert "ناقص" in partial["channels"]
    assert "غير مهيّأ" in alert_status(AlertSettings())["channels"]


# ------------------- اختبار تكامل حقيقي عبر HTTP (سوكِتات فعلية) ------------------- #

def test_end_to_end_over_real_http(monkeypatch, tmp_path):
    """يشغّل خادمًا محليًا يلعب دور Telegram API ويتأكد أن التنبيه يصل فعلًا.

    هذا اختبار تكامل حقيقي: يمرّ عبر httpx → مقبس TCP → خادم HTTP → تحليل JSON.
    """
    import http.server
    import threading

    received: list[dict] = []

    class FakeTelegram(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            received.append({"path": self.path, "body": body})
            payload = json.dumps({"ok": True, "result": {"message_id": 7}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args) -> None:  # إسكات سجل الخادم
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), FakeTelegram)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    try:
        import importlib

        import app.alerts as alerts_module

        monkeypatch.setenv("TELEGRAM_API_BASE", base)
        importlib.reload(alerts_module)  # يقرأ المتغير عند الاستيراد

        alerts_module.db.init_db()
        cfg = alerts_module.AlertSettings(
            enabled=True, telegram_bot_token=TOKEN, telegram_chat_id=CHAT
        )
        sent = run_sync(
            alerts_module.notify(
                Target(id="t9", name="مدونة", url="https://example.com"),
                {"ok": False, "status_code": 503, "reason": "الخدمة غير متاحة", "ts": time.time()},
                alerts_module.KIND_DOWN,
                cfg,
                retry_wait=0,
            )
        )
    finally:
        server.shutdown()
        server.server_close()

    assert sent is True
    assert len(received) == 1
    assert received[0]["path"] == f"/bot{TOKEN}/sendMessage"
    body = received[0]["body"]
    assert body["chat_id"] == CHAT and body["parse_mode"] == "HTML"
    assert "503" in body["text"] and "الخدمة غير متاحة" in body["text"]
