"""اختبارات E2E للوحة المراقبة — تعمل محليًا وعلى BrowserStack بلا تغيير في الكود."""

from __future__ import annotations

import json
import urllib.request

import pytest


def api(base_url: str, path: str) -> dict:
    with urllib.request.urlopen(f"{base_url}{path}", timeout=15) as response:
        return json.load(response)


def test_api_contract_without_browser(base_url):
    """عقد الـ API — يعمل بلا متصفح، فيتحقق من اللوحة حتى في بيئات بلا Chromium."""
    status = api(base_url, "/api/status")
    assert status["targets"], "لا توجد أهداف في /api/status"
    assert status["settings"]["storage"] in ("sqlite", "postgresql")

    for target in status["targets"]:
        assert {"id", "name", "url", "interval_seconds", "stats"} <= set(target)

    domains = api(base_url, "/api/config/domains")["owned_domains"]
    assert "127.0.0.1" in domains  # الفحص الذاتي المحلي

    first_id = status["targets"][0]["id"]
    checks = api(base_url, f"/api/targets/{first_id}/checks?limit=5")["checks"]
    assert isinstance(checks, list)


def test_dashboard_loads(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    assert "Adloab" in page.title()
    assert page.locator("h1").inner_text().strip() == "Adloab Uptime"
    # الاتجاه من اليمين لليسار
    assert page.locator("html").get_attribute("dir") == "rtl"


def test_tiles_and_cards_render(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    for tile in ["t-targets", "t-uptime", "t-latency", "t-incidents"]:
        assert page.locator(f"#{tile}").is_visible(), f"البطاقة {tile} غير ظاهرة"

    # بطاقة واحدة على الأقل لكل هدف مُعدّ في config/targets.yaml
    targets = api(base_url, "/api/status")["targets"]
    expect_cards = len([t for t in targets if t["enabled"]])
    page.wait_for_selector(".card", timeout=15000)
    assert page.locator(".card").count() == expect_cards

    # كل بطاقة تحمل شارة حالة
    assert page.locator(".card .badge").count() == expect_cards


def test_domain_allowlist_visible(page, base_url):
    """الشفافية: اللوحة تعرض النطاقات المسموح بفحصها فقط."""
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector("#domains .chip", timeout=15000)
    chips = page.locator("#domains .chip").all_inner_texts()
    allowed = api(base_url, "/api/config/domains")["owned_domains"]
    assert sorted(chips) == sorted(allowed)
    assert allowed, "قائمة النطاقات المسموح بها فارغة"


def test_manual_check_button(page, base_url):
    """زر «افحص الآن» يطلق فحصًا فوريًا ويعيد النتيجة."""
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector("[data-check]", timeout=15000)
    button = page.locator("[data-check]").first
    button.click()
    # بعد الفحص يُعاد رسم اللوحة ويظهر وقت تحديث جديد
    page.wait_for_function(
        "() => document.querySelector('#last-update').textContent.includes('آخر تحديث')",
        timeout=20000,
    )
    assert page.locator(".card").count() >= 1


def test_no_console_errors(page, base_url, console_errors):
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector(".card", timeout=15000)
    assert console_errors == [], f"أخطاء في المتصفح: {console_errors}"


@pytest.mark.parametrize("viewport", [{"width": 390, "height": 844}, {"width": 768, "height": 1024}])
def test_responsive_layout(browser, base_url, viewport):
    """اللوحة تعمل على الجوال والتابلت (اختبار حجم نافذة)."""
    context = browser.new_context(viewport=viewport, locale="ar-MA")
    page = context.new_page()
    try:
        page.goto(base_url, wait_until="networkidle")
        page.wait_for_selector(".card", timeout=15000)
        assert page.locator("h1").is_visible()
        # لا تمرير أفقي غير مقصود
        overflow = page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        assert overflow <= 2, f"تمرير أفقي بمقدار {overflow}px عند العرض {viewport['width']}px"
    finally:
        context.close()
