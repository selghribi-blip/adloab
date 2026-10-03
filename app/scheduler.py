"""المجدول: دورة خلفية تشغّل الفحوصات وفق فاصل كل هدف، مع سقف توازٍ وتنبيهات."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from . import store as db
from .alerts import (
    KIND_DOWN,
    KIND_SLOW,
    AlertSettings,
    evaluate_kinds,
    load_alert_settings,
    notify,
)
from .checker import make_client, run_check
from .config import Settings, Target

log = logging.getLogger("adloab.scheduler")


def _has_open_incident(target_id: str) -> bool:
    return any(i["target_id"] == target_id for i in db.incidents(limit=50, only_open=True))


async def _raise_alerts(
    target: Target, result: dict, alerts: AlertSettings, *, recovered: bool = False
) -> None:
    """إرسال التنبيهات المناسبة لهذا الفحص (مع احترام التهدئة والبطء المتتالي)."""
    for kind in evaluate_kinds(result, alerts, recovered=recovered):
        if kind == KIND_SLOW:
            # لا نُنبّه على ارتفاع عابر: ننتظر تكرار البطء latency_consecutive مرات
            streak = db.count_consecutive_slow(target.id, alerts.latency_alert_ms)
            if streak < alerts.latency_consecutive:
                log.info(
                    "بطء (%s ms) لكنه متكرر %s/%s مرة — لا تنبيه بعد",
                    round(float(result.get("total_ms") or 0)),
                    streak,
                    alerts.latency_consecutive,
                )
                continue
            result = {**result, "reason": f"بطء متكرر {streak} مرات متتالية · {result.get('reason') or ''}".strip(" ·")}
        await notify(target, result, kind, alerts)


async def check_target(
    client,
    target: Target,
    settings: Settings,
    alerts: AlertSettings | None = None,
) -> dict[str, Any]:
    """تنفيذ فحص هدف واحد وتخزينه وإدارة الحوادث والتنبيهات."""
    alerts = alerts or load_alert_settings()
    result = await run_check(client, target, settings)
    db.insert_check(target.id, result)

    if result["ok"]:
        recovered = _has_open_incident(target.id)
        if recovered:
            db.resolve_incidents(target.id)
        await _raise_alerts(target, result, alerts, recovered=recovered)
        log.info("OK   %-28s %sms", target.name, result.get("total_ms"))
    else:
        log.warning("FAIL %-28s %s", target.name, result.get("reason"))
        if db.consecutive_failures(target.id) >= settings.failure_threshold:
            had_incident = _has_open_incident(target.id)
            db.open_incident(target.id, result.get("reason") or "فشل غير معروف")
            if not had_incident:
                await notify(target, result, KIND_DOWN, alerts)
    return result


async def check_all(
    settings: Settings, targets: list[Target], alerts: AlertSettings | None = None
) -> list[dict[str, Any]]:
    """فحص كل الأهداف المفعّلة مرة واحدة (يُستخدم في CLI وGitHub Actions)."""
    alerts = alerts or load_alert_settings()
    semaphore = asyncio.Semaphore(settings.concurrency)

    async with make_client(settings) as client:

        async def guarded(target: Target) -> dict[str, Any]:
            async with semaphore:
                try:
                    return await check_target(client, target, settings, alerts)
                except Exception as exc:  # noqa: BLE001
                    log.exception("خطأ غير متوقع في فحص %s: %s", target.name, exc)
                    return {"ok": False, "reason": str(exc)}

        return await asyncio.gather(*(guarded(t) for t in targets if t.enabled))


async def loop(
    settings: Settings,
    targets: list[Target],
    stop: asyncio.Event,
    alerts: AlertSettings | None = None,
) -> None:
    """حلقة لا نهائية: تُشغّل كل هدف وفق فاصله الزمني الخاص."""
    alerts = alerts or load_alert_settings()
    semaphore = asyncio.Semaphore(settings.concurrency)
    next_run = {t.id: 0.0 for t in targets if t.enabled}

    async with make_client(settings) as client:
        while not stop.is_set():
            now = time.time()
            due = [t for t in targets if t.enabled and next_run.get(t.id, 0) <= now]

            async def guarded(target: Target) -> None:
                async with semaphore:
                    try:
                        await check_target(client, target, settings, alerts)
                    except Exception as exc:  # noqa: BLE001
                        log.exception("خطأ في فحص %s: %s", target.name, exc)
                    finally:
                        next_run[target.id] = time.time() + target.interval_seconds

            if due:
                await asyncio.gather(*(guarded(t) for t in due))
            try:
                await asyncio.wait_for(stop.wait(), timeout=2)
            except asyncio.TimeoutError:
                continue
