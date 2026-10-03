"""المجدول: دورة خلفية تشغّل الفحوصات وفق فاصل كل هدف، مع سقف توازٍ."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from . import store as db
from .alerts import send_alert
from .checker import make_client, run_check
from .config import Settings, Target

log = logging.getLogger("adloab.scheduler")


async def check_target(client, target: Target, settings: Settings) -> dict[str, Any]:
    """تنفيذ فحص هدف واحد وتخزينه وإدارة الحوادث والتنبيهات."""
    result = await run_check(client, target, settings)
    db.insert_check(target.id, result)

    if result["ok"]:
        if db.incidents(only_open=True) and any(
            i["target_id"] == target.id for i in db.incidents(only_open=True)
        ):
            db.resolve_incidents(target.id)
            await send_alert(target, result, settings)
        log.info("OK   %-28s %sms", target.name, result.get("total_ms"))
    else:
        log.warning("FAIL %-28s %s", target.name, result.get("reason"))
        if db.consecutive_failures(target.id) >= settings.failure_threshold:
            before = db.incidents(only_open=True)
            db.open_incident(target.id, result.get("reason") or "فشل غير معروف")
            after = db.incidents(only_open=True)
            if len(after) > len(before):
                await send_alert(target, result, settings)
    return result


async def check_all(settings: Settings, targets: list[Target]) -> list[dict[str, Any]]:
    """فحص كل الأهداف المفعّلة مرة واحدة (يُستخدم في CLI وGitHub Actions)."""
    semaphore = asyncio.Semaphore(settings.concurrency)

    async with make_client(settings) as client:

        async def guarded(target: Target) -> dict[str, Any]:
            async with semaphore:
                try:
                    return await check_target(client, target, settings)
                except Exception as exc:  # noqa: BLE001
                    log.exception("خطأ غير متوقع في فحص %s: %s", target.name, exc)
                    return {"ok": False, "reason": str(exc)}

        return await asyncio.gather(*(guarded(t) for t in targets if t.enabled))


async def loop(settings: Settings, targets: list[Target], stop: asyncio.Event) -> None:
    """حلقة لا نهائية: تُشغّل كل هدف وفق فاصله الزمني الخاص."""
    semaphore = asyncio.Semaphore(settings.concurrency)
    next_run = {t.id: 0.0 for t in targets if t.enabled}

    async with make_client(settings) as client:
        while not stop.is_set():
            now = time.time()
            due = [t for t in targets if t.enabled and next_run.get(t.id, 0) <= now]

            async def guarded(target: Target) -> None:
                async with semaphore:
                    try:
                        await check_target(client, target, settings)
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
