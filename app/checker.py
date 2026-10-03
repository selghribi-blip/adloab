"""محرّك الفحص: قياس زمن الاستجابة على مراحل + التحقق من المحتوى + شهادة TLS.

ملاحظة تصميمية: هذا الفحص موجّه لموقع *تملكه* — طلب واحد لكل دورة،
مع تعريف واضح بالهوية، وبلا أي محاولة للتملّص من أنظمة الحماية.
"""

from __future__ import annotations

import asyncio
import socket
import ssl
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import Settings, Target


def _host_port(url: str) -> tuple[str, int, bool]:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    secure = parsed.scheme == "https"
    port = parsed.port or (443 if secure else 80)
    return host, port, secure


def dns_lookup_ms(host: str, port: int) -> float:
    start = time.perf_counter()
    socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return round((time.perf_counter() - start) * 1000, 1)


def tls_info(host: str, port: int, timeout: float) -> dict[str, Any]:
    """مصافحة TLS: زمن المصافحة + عدد الأيام المتبقية لانتهاء الشهادة."""
    info: dict[str, Any] = {"connect_ms": None, "tls_days_left": None, "tls_error": None}
    context = ssl.create_default_context()
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=host) as tls:
                info["connect_ms"] = round((time.perf_counter() - start) * 1000, 1)
                cert = tls.getpeercert()
        not_after = cert.get("notAfter")
        if not_after:
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            info["tls_days_left"] = round(
                (expiry - datetime.now(timezone.utc)).total_seconds() / 86400, 1
            )
    except Exception as exc:  # noqa: BLE001 - نُسجّل السبب ونكمل
        info["tls_error"] = f"{type(exc).__name__}: {exc}"
    return info


async def http_check(client: httpx.AsyncClient, target: Target, settings: Settings) -> dict[str, Any]:
    """فحص HTTP واحد مع تفصيل الأزمنة: DNS → اتصال/‏TLS → أول بايت → اكتمال."""
    result: dict[str, Any] = {
        "ts": time.time(),
        "ok": False,
        "status_code": None,
        "reason": "",
        "dns_ms": None,
        "connect_ms": None,
        "ttfb_ms": None,
        "total_ms": None,
        "tls_days_left": None,
        "browser_ms": None,
        "browser_note": None,
    }
    host, port, secure = _host_port(target.url)

    try:
        result["dns_ms"] = await asyncio.to_thread(dns_lookup_ms, host, port)
    except Exception as exc:  # noqa: BLE001
        result["reason"] = f"فشل تحليل DNS: {exc}"
        return result

    # فحص TLS معلوماتي: قد يفشل داخل بيئات تُمرّر الاتصال عبر وسيط (proxy)
    # بينما ينجح طلب HTTPS نفسه — لذلك لا نُسقط الفحص بسببه، بل نستخدمه للتشخيص.
    tls_error = None
    if secure and target.check_tls:
        tls = await asyncio.to_thread(tls_info, host, port, settings.timeout_seconds)
        result["connect_ms"] = tls["connect_ms"]
        result["tls_days_left"] = tls["tls_days_left"]
        tls_error = tls["tls_error"]

    start = time.perf_counter()
    try:
        async with client.stream(target.method, target.url) as response:
            result["ttfb_ms"] = round((time.perf_counter() - start) * 1000, 1)
            result["status_code"] = response.status_code
            body = bytearray()
            limit = settings.max_body_kb * 1024
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) >= limit:
                    break
        result["total_ms"] = round((time.perf_counter() - start) * 1000, 1)
    except httpx.TimeoutException:
        result["reason"] = f"انتهت المهلة ({settings.timeout_seconds:.0f} ثانية)"
        if tls_error:
            result["reason"] += f" · مصافحة TLS المباشرة فشلت أيضًا ({tls_error})"
        return result
    except Exception as exc:  # noqa: BLE001
        result["reason"] = f"{type(exc).__name__}: {exc}"
        if tls_error:
            result["reason"] += f" · TLS: {tls_error}"
        return result

    problems: list[str] = []
    if result["status_code"] not in target.expect_status:
        expected = "/".join(str(s) for s in target.expect_status)
        problems.append(f"رمز الحالة {result['status_code']} بدلًا من {expected}")
    if target.expect_text:
        text = body.decode("utf-8", errors="ignore")
        if target.expect_text not in text:
            problems.append(f"النص المتوقع «{target.expect_text}» غير موجود في الصفحة")
    if result["tls_days_left"] is not None and result["tls_days_left"] < 7:
        problems.append(f"شهادة SSL تنتهي خلال {result['tls_days_left']} يوم")

    result["ok"] = not problems
    result["reason"] = " · ".join(problems)
    return result


async def browser_check(url: str, timeout: float) -> dict[str, Any]:
    """فحص اختياري بمتصفح حقيقي (Playwright) لمواقع تعتمد على JavaScript.

    يتطلب: pip install playwright && playwright install chromium
    مفيد لموقعك الخاص: يرصد أخطاء الـ console، عنوان الصفحة، وزمن التحميل الكامل.
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError:
        return {"browser_ms": None, "browser_note": "Playwright غير مثبّت (فحص المتصفح معطّل)"}

    console_errors: list[str] = []
    start = time.perf_counter()
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            title = await page.title()
            await browser.close()
    except Exception as exc:  # noqa: BLE001
        return {"browser_ms": None, "browser_note": f"فشل فحص المتصفح: {type(exc).__name__}: {exc}"}

    elapsed = round((time.perf_counter() - start) * 1000, 1)
    note = f"العنوان: {title}"
    if console_errors:
        note += f" · أخطاء console: {len(console_errors)} ({console_errors[0][:80]})"
    return {"browser_ms": elapsed, "browser_note": note}


def make_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(settings.timeout_seconds),
        headers={"User-Agent": settings.user_agent, "Accept-Language": "ar,en;q=0.8"},
        verify=True,
    )


async def run_check(
    client: httpx.AsyncClient, target: Target, settings: Settings
) -> dict[str, Any]:
    """فحص كامل لهدف واحد (HTTP + متصفح إن كان مفعّلًا)."""
    result = await http_check(client, target, settings)
    if target.browser_check and result["ok"]:
        browser = await browser_check(target.url, settings.timeout_seconds)
        result.update(browser)
    return result
