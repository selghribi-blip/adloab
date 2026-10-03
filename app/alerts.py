"""التنبيهات: Telegram Bot API + Webhook عام + حماية من الإغراق (cooldown).

المصادر (بترتيب الأولوية):
  1) متغيرات البيئة: TELEGRAM_BOT_TOKEN · TELEGRAM_CHAT_ID · ALERT_WEBHOOK_URL
  2) ملف config/alerts.yaml (غير السرّي منه فقط)

قاعدة أمنية: لا تُخزَّن رموز البوت في Git أبدًا. ضعها في `.env` (مستبعد في .gitignore)
أو في GitHub Secrets عند التشغيل عبر Actions.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

from . import store as db
from .config import CONFIG_DIR, Target

log = logging.getLogger("adloab.alerts")

ALERTS_FILE = CONFIG_DIR / "alerts.yaml"
# قابل للتغيير عبر TELEGRAM_API_BASE (للاختبارات أو للعمل خلف وسيط/بروكسي)
TELEGRAM_API = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")

# أنواع التنبيهات وفترات التهدئة الافتراضية (بالثواني)
KIND_DOWN = "down"
KIND_UP = "up"
KIND_SLOW = "slow"
KIND_TLS = "tls"
KIND_TEST = "test"

DEFAULT_COOLDOWN = {
    KIND_DOWN: 0,      # التوقف يُبلَّغ فورًا (مرة لكل حادثة — تحكمه إدارة الحوادث)
    KIND_UP: 0,        # العودة للعمل فورًا
    KIND_SLOW: 1800,   # بطء الأداء: مرة كل نصف ساعة لكل هدف
    KIND_TLS: 86400,   # قرب انتهاء الشهادة: مرة كل يوم
}


@dataclass
class AlertSettings:
    enabled: bool = True
    webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_disable_notification: bool = False
    telegram_topic_id: str = ""          # للقروبات ذات المواضيع (message_thread_id)
    latency_alert_ms: float = 0.0        # 0 = معطّل؛ مثلاً 2000 يعني تنبيه إن تجاوز الطلب 2 ثانية
    latency_consecutive: int = 3         # عدد المرات المتتالية قبل تنبيه البطء
    tls_warn_days: float = 7.0           # تنبيه قبل انتهاء الشهادة بهذا العدد من الأيام
    cooldown_seconds: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_COOLDOWN))

    @property
    def telegram_ready(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def _from_yaml() -> dict:
    if not ALERTS_FILE.exists():
        return {}
    try:
        return yaml.safe_load(ALERTS_FILE.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        log.error("تعذّر قراءة %s: %s", ALERTS_FILE, exc)
        return {}


def load_alert_settings() -> AlertSettings:
    """دمج الإعدادات: البيئة تتقدّم على الملف، والملف يتقدّم على الافتراضيات."""
    raw = _from_yaml()
    telegram = raw.get("telegram") or {}
    webhook = raw.get("webhook") or {}

    env_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    env_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    env_webhook = os.getenv("ALERT_WEBHOOK_URL", "").strip()

    cooldown = dict(DEFAULT_COOLDOWN)
    cooldown.update({str(k): int(v) for k, v in (raw.get("cooldown_seconds") or {}).items()})

    settings = AlertSettings(
        enabled=bool(raw.get("enabled", True)),
        webhook_url=env_webhook or str(webhook.get("url", "") or ""),
        telegram_bot_token=env_token or str(telegram.get("bot_token", "") or ""),
        telegram_chat_id=env_chat or str(telegram.get("chat_id", "") or ""),
        telegram_disable_notification=bool(telegram.get("silent", False)),
        telegram_topic_id=str(telegram.get("message_thread_id", "") or ""),
        latency_alert_ms=float(raw.get("latency_alert_ms", 0) or 0),
        latency_consecutive=max(1, int(raw.get("latency_consecutive", 3))),
        tls_warn_days=float(raw.get("tls_warn_days", 7) or 0),
        cooldown_seconds=cooldown,
    )
    if not settings.enabled:
        log.info("التنبيهات معطّلة من الإعدادات (enabled: false)")
    return settings


# --------------------------------------------------------------------------- #
#  بناء الرسائل
# --------------------------------------------------------------------------- #

_KIND_TITLES = {
    KIND_DOWN: "🔴 توقف الموقع",
    KIND_UP: "🟢 عودة للعمل",
    KIND_SLOW: "🐢 بطء في الأداء",
    KIND_TLS: "🔐 شهادة SSL تقترب من الانتهاء",
    KIND_TEST: "🧪 رسالة تجريبية",
}


def _fmt_time(ts: float | None = None) -> str:
    moment = datetime.fromtimestamp(ts or time.time(), tz=timezone.utc)
    return moment.strftime("%Y-%m-%d %H:%M:%S UTC")


def build_alert_text(target: Target | None, result: dict, kind: str) -> str:
    """رسالة HTML جاهزة لـ Telegram (بلا Markdown هشّ)."""
    title = _KIND_TITLES.get(kind, kind)
    lines = [f"<b>{title}</b>"]

    if target is not None:
        lines.append(f"<b>الهدف:</b> {html.escape(target.name)}")
        lines.append(f"<b>الرابط:</b> {html.escape(target.url)}")

    if kind != KIND_TEST:
        if result.get("status_code") is not None:
            lines.append(f"<b>رمز الحالة:</b> <code>{result['status_code']}</code>")
        if result.get("reason"):
            lines.append(f"<b>السبب:</b> {html.escape(str(result['reason'])[:400])}")
        if result.get("total_ms") is not None:
            lines.append(f"<b>زمن الاستجابة:</b> {round(float(result['total_ms']))} ms")
        if kind == KIND_TLS and result.get("tls_days_left") is not None:
            lines.append(f"<b>متبقٍ للشهادة:</b> {round(float(result['tls_days_left']))} يوم")
        if result.get("dns_ms") is not None or result.get("ttfb_ms") is not None:
            lines.append(
                f"<b>التفصيل:</b> DNS {result.get('dns_ms') or '—'} ms · "
                f"TTFB {result.get('ttfb_ms') or '—'} ms"
            )
        lines.append(f"<b>الوقت:</b> {_fmt_time(result.get('ts'))}")
    else:
        lines.append("قناة التنبيهات تعمل بنجاح ✅")

    lines.append("\n<i>Adloab Uptime — مراقبة مواقعك</i>")
    return "\n".join(lines)


def build_plain_text(target: Target | None, result: dict, kind: str) -> str:
    """نسخة نصية بسيطة (Slack / Discord / Ntfy)."""
    title = _KIND_TITLES.get(kind, kind)
    parts = [title]
    if target is not None:
        parts.append(f"{target.name} — {target.url}")
    if result.get("reason"):
        parts.append(f"السبب: {result['reason']}")
    if result.get("status_code") is not None:
        parts.append(f"الرمز: {result['status_code']}")
    if result.get("total_ms") is not None:
        parts.append(f"الزمن: {round(float(result['total_ms']))} ms")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
#  الإرسال
# --------------------------------------------------------------------------- #

async def send_telegram(
    text: str,
    settings: AlertSettings,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
    retry_wait: float = 2.0,
) -> bool:
    """إرسال رسالة عبر Telegram Bot API مع إعادة محاولة عند 429/5xx.

    `transport` يُستخدم في الاختبارات لتوجيه الطلب إلى خادم وهمي.
    """
    if not settings.telegram_ready:
        log.debug("Telegram غير مهيّأ — تخطّي الإرسال")
        return False

    url = f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/sendMessage"
    payload: dict = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "disable_notification": settings.telegram_disable_notification,
    }
    if settings.telegram_topic_id:
        payload["message_thread_id"] = settings.telegram_topic_id

    for attempt in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=15, transport=transport) as client:
                response = await client.post(url, json=payload)
            if response.status_code == 200:
                log.info("✅ أُرسل تنبيه Telegram")
                return True
            if response.status_code == 429:
                wait = 3
                try:
                    wait = int((response.json().get("parameters") or {}).get("retry_after", 3))
                except Exception:  # noqa: BLE001
                    pass
                log.warning("Telegram: تجاوز الحد (429) — إعادة المحاولة بعد %ss", wait)
                await asyncio.sleep(min(wait, 30))
                continue
            if response.status_code in (401, 403, 404):
                log.error(
                    "Telegram رفض الطلب (%s): تحقق من صلاحية التوكن ورقم المحادثة. %s",
                    response.status_code,
                    response.text[:200],
                )
                return False
            log.warning("Telegram: رد غير متوقع %s — %s", response.status_code, response.text[:200])
        except Exception as exc:  # noqa: BLE001
            log.warning("تعذّر الاتصال بـ Telegram (محاولة %s/3): %s", attempt, exc)
        await asyncio.sleep(retry_wait * attempt)
    return False


async def send_webhook(
    payload: dict,
    settings: AlertSettings,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> bool:
    """Webhook عام متوافق مع Slack وDiscord وNtfy وTelegram-webhook."""
    if not settings.webhook_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=10, transport=transport) as client:
            response = await client.post(settings.webhook_url, json=payload)
        if response.status_code < 400:
            log.info("✅ أُرسل التنبيه عبر Webhook")
            return True
        log.warning("Webhook: رد %s — %s", response.status_code, response.text[:200])
    except Exception as exc:  # noqa: BLE001
        log.error("تعذّر إرسال Webhook: %s", exc)
    return False


async def notify(
    target: Target | None,
    result: dict,
    kind: str,
    settings: AlertSettings,
    *,
    force: bool = False,
    transport: httpx.AsyncBaseTransport | None = None,
    retry_wait: float = 2.0,
) -> bool:
    """إرسال تنبيه واحد مع احترام التهدئة. يُرجع True إذا أُرسل فعلًا.

    `force=True` يتجاوز التهدئة (يُستخدم في الرسالة التجريبية).
    """
    if not settings.enabled and not force:
        return False

    target_id = target.id if target is not None else "self"
    cooldown = int(settings.cooldown_seconds.get(kind, 0))

    if not force and cooldown > 0:
        last = db.alert_last_sent(target_id, kind)
        if last is not None and (time.time() - last) < cooldown:
            log.info(
                "تنبيه «%s» لـ %s داخل فترة التهدئة (%s ثانية) — لا إرسال",
                kind,
                target_id,
                cooldown,
            )
            return False

    text_html = build_alert_text(target, result, kind)
    text_plain = build_plain_text(target, result, kind)

    sent = False
    if settings.telegram_ready:
        sent = await send_telegram(text_html, settings, transport=transport, retry_wait=retry_wait) or sent
    if settings.webhook_url:
        payload = {"text": text_html, "content": text_plain, "message": text_plain}
        sent = await send_webhook(payload, settings, transport=transport) or sent

    log.warning("ALERT | %s", text_plain.replace("\n", " | "))
    if sent:
        db.alert_mark_sent(target_id, kind)
    return sent


def evaluate_kinds(result: dict, settings: AlertSettings, *, recovered: bool = False) -> list[str]:
    """ما أنواع التنبيهات التي يستحقها هذا الفحص؟"""
    kinds: list[str] = []
    if recovered:
        kinds.append(KIND_UP)
        return kinds
    if not result.get("ok"):
        kinds.append(KIND_DOWN)
        return kinds

    days = result.get("tls_days_left")
    if settings.tls_warn_days and days is not None and float(days) <= settings.tls_warn_days:
        kinds.append(KIND_TLS)

    if settings.latency_alert_ms and result.get("total_ms") is not None:
        if float(result["total_ms"]) >= settings.latency_alert_ms:
            kinds.append(KIND_SLOW)
    return kinds


def alert_status(settings: AlertSettings) -> dict:
    """ملخّص حالة قناة التنبيهات (يُعرض في اللوحة و`cli status`)."""
    parts = []
    if settings.telegram_ready:
        # لا نكشف التوكن: نعرض 4 أحرف فقط للتأكد من أنه الصحيح
        tail = settings.telegram_bot_token[-4:]
        parts.append(f"Telegram ✅ (…{tail} → chat {settings.telegram_chat_id})")
    elif settings.telegram_bot_token or settings.telegram_chat_id:
        parts.append("Telegram ⚠️ ناقص: يجب ضبط التوكن ورقم المحادثة معًا")
    else:
        parts.append("Telegram ⚪ غير مهيّأ")
    parts.append("Webhook ✅" if settings.webhook_url else "Webhook ⚪ غير مهيّأ")
    if settings.latency_alert_ms:
        parts.append(f"تنبيه البطء ≥ {round(settings.latency_alert_ms)} ms")
    return {"channels": " · ".join(parts)}
