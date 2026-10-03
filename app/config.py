"""إعدادات النظام + حاجز الملكية (Ownership Guard).

لا يُسمح بفحص أي نطاق غير موجود في config/owned_domains.yaml
أو غير مصرّح به صراحةً عبر متغير البيئة ADLOAB_EXTRA_DOMAINS.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
TARGETS_FILE = CONFIG_DIR / "targets.yaml"
DOMAINS_FILE = CONFIG_DIR / "owned_domains.yaml"

DATA_DIR.mkdir(exist_ok=True)


class ConfigurationError(RuntimeError):
    """خطأ في ملفات الإعداد."""


class NotOwnedError(PermissionError):
    """محاولة فحص نطاق غير موجود في قائمة الملكية."""


@dataclass(frozen=True)
class Settings:
    concurrency: int = 4
    timeout_seconds: float = 15.0
    user_agent: str = "AdloabUptimeBot/1.0 (uptime monitoring; owner-verified)"
    max_body_kb: int = 64
    failure_threshold: int = 2


@dataclass(frozen=True)
class Target:
    id: str
    name: str
    url: str
    interval_seconds: int = 300
    method: str = "GET"
    expect_status: tuple[int, ...] = (200,)
    expect_text: str = ""
    check_tls: bool = True
    browser_check: bool = False
    enabled: bool = True


def _host_of(url: str) -> str:
    from urllib.parse import urlparse

    parsed = urlparse(url if "://" in url else f"https://{url}")
    if not parsed.hostname:
        raise ConfigurationError(f"رابط غير صالح: {url}")
    return parsed.hostname.lower()


def load_owned_domains() -> set[str]:
    """قراءة قائمة النطاقات المملوكة + أي نطاقات إضافية من متغير البيئة."""
    domains: set[str] = set()
    if DOMAINS_FILE.exists():
        raw = yaml.safe_load(DOMAINS_FILE.read_text(encoding="utf-8")) or []
        domains.update(str(d).strip().lower() for d in raw if str(d).strip())

    extra = os.getenv("ADLOAB_EXTRA_DOMAINS", "")
    domains.update(part.strip().lower() for part in extra.split(",") if part.strip())
    return domains


def domain_allowed(host: str, owned: set[str]) -> bool:
    """النطاق مسموح إذا طابق عنصرًا في القائمة هو نفسه أو نطاقًا فرعيًا منه."""
    host = host.lower().strip(".")
    return any(host == d or host.endswith("." + d) for d in owned)


def assert_allowed(url: str, owned: set[str] | None = None) -> str:
    """يرفع NotOwnedError إذا لم يكن النطاق ضمن قائمة الملكية."""
    owned = load_owned_domains() if owned is None else owned
    host = _host_of(url)
    if not domain_allowed(host, owned):
        raise NotOwnedError(
            f"النطاق «{host}» غير موجود في config/owned_domains.yaml. "
            "أضف فقط النطاقات التي تملكها أو لديك إذن صريح بفحصها."
        )
    return host


def load_targets() -> tuple[Settings, list[Target]]:
    """تحميل الإعدادات والأهداف مع التحقق من قائمة الملكية."""
    if not TARGETS_FILE.exists():
        raise ConfigurationError(f"ملف الأهداف غير موجود: {TARGETS_FILE}")

    raw = yaml.safe_load(TARGETS_FILE.read_text(encoding="utf-8")) or {}
    settings = Settings(**(raw.get("settings") or {}))

    owned = load_owned_domains()
    targets: list[Target] = []
    for index, item in enumerate(raw.get("targets") or []):
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        host = assert_allowed(url, owned)  # ← حاجز الملكية
        statuses = item.get("expect_status") or [200]
        targets.append(
            Target(
                id=f"t{index}-{host.replace('.', '-')}",
                name=str(item.get("name") or host),
                url=url,
                interval_seconds=max(30, int(item.get("interval_seconds", 300))),
                method=str(item.get("method", "GET")).upper(),
                expect_status=tuple(int(s) for s in statuses),
                expect_text=str(item.get("expect_text") or ""),
                check_tls=bool(item.get("check_tls", True)),
                browser_check=bool(item.get("browser_check", False)),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return settings, targets
