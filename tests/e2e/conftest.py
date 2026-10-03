"""تجهيزات اختبارات E2E — تعمل في ثلاثة أوضاع:

1) محلي بمتصفح Chromium مثبّت (افتراضي): يشغّل اللوحة على منفذ مؤقت ويختبرها.
2) موقع خارجي: E2E_BASE_URL=https://staging.mysite.ma
3) BrowserStack (متصفحات وأجهزة حقيقية): عيّن BROWSERSTACK_USERNAME و BROWSERSTACK_ACCESS_KEY
   واختياريًا BROWSERSTACK_BROWSER / BROWSERSTACK_OS / BROWSERSTACK_OS_VERSION.

إن لم يتوفر أي منها تتخطى الاختبارات نفسها (skip) بدل أن تفشل.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

LOCAL_PORT = int(os.getenv("E2E_LOCAL_PORT", "8765"))
STARTUP_TIMEOUT = 40

# الترتيب مهم: تحميل Playwright اختياري كي تُتخطّى الاختبارات بلطف عند عدم تثبيته
playwright_sync = pytest.importorskip("playwright.sync_api", reason="playwright غير مثبّت")
sync_playwright = playwright_sync.sync_playwright


def _wait_http(url: str, timeout: int = STARTUP_TIMEOUT) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    return False


def _port_free(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


@pytest.fixture(scope="session")
def base_url() -> str:
    """عنوان اللوحة المفحوصة: خارجي إن حُدد، وإلا نسخة محلية مؤقتة."""
    external = os.getenv("E2E_BASE_URL", "").strip()
    if external:
        if not _wait_http(f"{external.rstrip('/')}/healthz"):
            pytest.skip(f"الموقع الخارجي غير متاح: {external}")
        return external.rstrip("/")

    port = LOCAL_PORT
    while not _port_free(port):
        port += 1

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    if not _wait_http(f"{url}/healthz"):
        process.terminate()
        pytest.skip("تعذّر تشغيل اللوحة محليًا لاختبار E2E")

    yield url

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:  # pragma: no cover
        process.kill()


@pytest.fixture(scope="session")
def playwright():
    # مهم: سياق Playwright المتزامن يشغّل حلقة أحداث في الخيط الحالي،
    # لذا نتخطى قبل فتحه حتى لا نُفسد اختبارات أخرى تستخدم asyncio.
    if not _any_browser_available():
        pytest.skip(
            "لا يوجد متصفح: ثبّته بالأمر «playwright install --with-deps chromium» "
            "أو عيّن بيانات BrowserStack"
        )
    with sync_playwright() as instance:
        yield instance


def _browserstack_credentials() -> tuple[str, str] | None:
    user = os.getenv("BROWSERSTACK_USERNAME", "").strip()
    key = os.getenv("BROWSERSTACK_ACCESS_KEY", "").strip()
    return (user, key) if user and key else None


def _chromium_installed() -> bool:
    """هل يوجد متصفح محلي؟ (نفحص قبل فتح سياق Playwright لنتخطى بسرعة وبلا آثار جانبية)."""
    root = Path(
        os.getenv("PLAYWRIGHT_BROWSERS_PATH") or (Path.home() / ".cache" / "ms-playwright")
    )
    if not root.exists():
        return False
    return any(
        entry.name.startswith(("chromium-", "chromium_headless_shell-", "chrome-"))
        for entry in root.iterdir()
    )


def _any_browser_available() -> bool:
    return _browserstack_credentials() is not None or _chromium_installed()


def _connect_browserstack(playwright, credentials: tuple[str, str]):
    """الاتصال بمتصفح حقيقي على BrowserStack عبر Playwright CDP."""
    user, key = credentials
    browser_name = os.getenv("BROWSERSTACK_BROWSER", "chrome").lower()
    caps = {
        "browser": browser_name,
        "browser_version": os.getenv("BROWSERSTACK_BROWSER_VERSION", "latest"),
        "os": os.getenv("BROWSERSTACK_OS", "Windows"),
        "os_version": os.getenv("BROWSERSTACK_OS_VERSION", "11"),
        "name": os.getenv("E2E_TEST_NAME", "Adloab Uptime — e2e"),
        "build": os.getenv("BROWSERSTACK_BUILD", "adloab-local"),
        "project": "adloab-uptime",
        "browserstack.username": user,
        "browserstack.accessKey": key,
        "browserstack.debug": True,
        # لازم عند اختبار خادم محلي/خاص عبر أنفاق BrowserStack
        "local": os.getenv("BROWSERSTACK_LOCAL", "false").lower() == "true",
    }
    endpoint = "wss://cdp.browserstack.com/playwright?caps=" + urllib.parse.quote(
        json.dumps(caps)
    )
    engine = {
        "chrome": playwright.chromium,
        "edge": playwright.chromium,
        "chromium": playwright.chromium,
        "firefox": playwright.firefox,
        "safari": playwright.webkit,
        "webkit": playwright.webkit,
    }.get(browser_name, playwright.chromium)
    return engine.connect(endpoint)


@pytest.fixture(scope="session")
def browser(playwright):
    credentials = _browserstack_credentials()
    if credentials:
        print(f"\n🌍 BrowserStack: {os.getenv('BROWSERSTACK_BROWSER', 'chrome')} "
              f"على {os.getenv('BROWSERSTACK_OS', 'Windows')}")
        browser = _connect_browserstack(playwright, credentials)
        yield browser
        browser.close()
        return

    try:
        browser = playwright.chromium.launch(headless=True)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(
            "تعذّر تشغيل المتصفح المحلي. ثبّته بالأمر: playwright install --with-deps chromium "
            f"({type(exc).__name__})"
        )
    yield browser
    browser.close()


@pytest.fixture()
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="ar-MA")
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture()
def console_errors(page) -> list[str]:
    """تجميع أخطاء الـ console خلال الاختبار."""
    errors: list[str] = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    return errors
