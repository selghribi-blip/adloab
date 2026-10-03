"""واجهة سطر الأوامر: فحص واحد لمرة واحدة (مثالي لـ cron / GitHub Actions).

أمثلة:
    python -m app.cli check            # فحص كل الأهداف
    python -m app.cli check --json     # النتيجة بصيغة JSON
    python -m app.cli status           # ملخّص آخر 24 ساعة
    python -m app.cli domains          # النطاقات المسموح بفحصها
    python -m app.cli test-alert       # إرسال رسالة تجريبية إلى Telegram
    python -m app.cli telegram-id      # معرفة رقم محادثتك (chat_id)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx

from . import store as db
from .alerts import alert_status, load_alert_settings, notify
from .config import load_owned_domains, load_targets
from .scheduler import check_all


async def _run_check(as_json: bool) -> int:
    db.init_db()
    settings, targets = load_targets()
    for target in targets:
        db.upsert_target(target.id, target.name, target.url, target.interval_seconds, target.enabled)
    results = await check_all(settings, targets)

    if as_json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        for target, result in zip([t for t in targets if t.enabled], results):
            mark = "✅" if result.get("ok") else "❌"
            print(
                f"{mark} {target.name:<28} "
                f"{(result.get('total_ms') or 0):>7} ms  "
                f"{result.get('status_code') or '-'}  {result.get('reason') or ''}"
            )

    failed = [r for r in results if not r.get("ok")]
    return 1 if failed else 0


def _run_status() -> int:
    db.init_db()
    _, targets = load_targets()
    latest = db.latest_checks([t.id for t in targets])
    print(f"{'الهدف':<28} {'الحالة':<8} {'التشغيل%':<9} {'متوسط ms':<10} {'SSL أيام'}")
    print("-" * 70)
    for target in targets:
        stats = db.window_stats(target.id, hours=24)
        last = latest.get(target.id)
        mark = "غير معروف" if not last else ("سليم" if last["ok"] else "متوقف")
        print(
            f"{target.name:<28} {mark:<8} "
            f"{(stats['uptime_pct'] if stats['uptime_pct'] is not None else 0):<9} "
            f"{(stats['avg_ms'] or 0):<10} "
            f"{stats['tls_days_left'] if stats['tls_days_left'] is not None else '-'}"
        )

    print("\nقنوات التنبيه: " + alert_status(load_alert_settings())["channels"])
    return 0


async def _run_test_alert() -> int:
    """إرسال رسالة تجريبية للتحقق من صحة التوكن ورقم المحادثة."""
    alerts = load_alert_settings()
    if not alerts.telegram_ready and not alerts.webhook_url:
        print("⚠️  لا توجد قناة تنبيه مهيّأة.\n")
        print("اضبط متغيرات البيئة أولًا (واحدة من الطرق):\n")
        print('  export TELEGRAM_BOT_TOKEN="123456:AA..."   # من @BotFather')
        print('  export TELEGRAM_CHAT_ID="123456789"        # من @userinfobot')
        print("\nأو املأ config/alerts.yaml، أو انسخ .env.example إلى .env واملأه.")
        return 2

    print("📨 القنوات: " + alert_status(alerts)["channels"])
    sent = await notify(
        None, {"ok": True, "ts": __import__("time").time()}, "test", alerts, force=True
    )
    if sent:
        print("✅ تم الإرسال — راجع Telegram الآن.")
        return 0
    print("❌ فشل الإرسال — راجع الرسائل أعلاه (تحقق من التوكن ومن أنك أرسلت /start للبوت).")
    return 1


async def _run_telegram_id() -> int:
    """معرفة chat_id: أرسل رسالة إلى بوتك ثم شغّل هذا الأمر."""
    alerts = load_alert_settings()
    if not alerts.telegram_bot_token:
        print("⚠️  اضبط TELEGRAM_BOT_TOKEN أولًا (من @BotFather).")
        return 2

    url = f"https://api.telegram.org/bot{alerts.telegram_bot_token}/getUpdates"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        print(f"❌ تعذّر الاتصال بـ Telegram: {exc}")
        return 1

    if not data.get("ok"):
        print(
            "❌ رفض Telegram الطلب — تأكد أن التوكن صحيح.\n"
            f"   الرد: {str(data)[:200]}"
        )
        return 1

    chats: dict[str, str] = {}
    for update in data.get("result", []):
        for key in ("message", "edited_message", "channel_post", "my_chat_member"):
            chat = (update.get(key) or {}).get("chat")
            if chat:
                label = chat.get("title") or " ".join(
                    filter(None, [chat.get("first_name"), chat.get("last_name")])
                )
                chats[str(chat["id"])] = f"{chat.get('type')} · {label or 'بلا اسم'}"

    if not chats:
        print(
            "لم أجد أي محادثة بعد.\n"
            "افتح Telegram ← ابحث عن بوتك ← اضغط Start وأرسل أي رسالة ← ثم أعد تشغيل الأمر."
        )
        return 3

    print("✅ المحادثات المتاحة (انسخ الرقم إلى TELEGRAM_CHAT_ID):\n")
    for chat_id, label in chats.items():
        print(f"   {chat_id}   ←  {label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adloab-uptime", description="نظام مراقبة المواقع")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="فحص الأهداف مرة واحدة")
    check.add_argument("--json", action="store_true", help="إخراج JSON")
    sub.add_parser("status", help="ملخّص آخر 24 ساعة")
    sub.add_parser("domains", help="عرض النطاقات المسموح بفحصها")
    sub.add_parser("test-alert", help="إرسال تنبيه تجريبي إلى قنوات التنبيه")
    sub.add_parser("telegram-id", help="عرض رقم محادثة Telegram (chat_id)")

    args = parser.parse_args(argv)
    if args.command == "check":
        return asyncio.run(_run_check(args.json))
    if args.command == "status":
        return _run_status()
    if args.command == "domains":
        print("\n".join(sorted(load_owned_domains())))
        return 0
    if args.command == "test-alert":
        return asyncio.run(_run_test_alert())
    if args.command == "telegram-id":
        return asyncio.run(_run_telegram_id())
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
