"""التنبيهات: سجل + Webhook (Slack / Discord / Telegram / Ntfy) — كلها بخطة مجانية."""

from __future__ import annotations

import logging

import httpx

from .config import Settings, Target

log = logging.getLogger("adloab.alerts")


def _severity(result: dict) -> str:
    return "🔴 توقف" if not result.get("ok") else "🟢 عودة للعمل"


def build_message(target: Target, result: dict) -> str:
    lines = [
        f"{_severity(result)} — {target.name}",
        f"الرابط: {target.url}",
    ]
    if result.get("status_code") is not None:
        lines.append(f"رمز الحالة: {result['status_code']}")
    if result.get("reason"):
        lines.append(f"السبب: {result['reason']}")
    if result.get("total_ms") is not None:
        lines.append(f"زمن الاستجابة: {result['total_ms']} مللي ثانية")
    if result.get("tls_days_left") is not None:
        lines.append(f"صلاحية الشهادة: {result['tls_days_left']} يوم")
    return "\n".join(lines)


async def send_alert(target: Target, result: dict, settings: Settings) -> None:
    message = build_message(target, result)
    log.warning("ALERT | %s", message.replace("\n", " | "))

    if not settings.alerts_enabled or not settings.alert_webhook:
        return

    payload: dict = {"text": message, "content": message, "message": message}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(settings.alert_webhook, json=payload)
    except Exception as exc:  # noqa: BLE001
        log.error("تعذّر إرسال التنبيه عبر Webhook: %s", exc)
