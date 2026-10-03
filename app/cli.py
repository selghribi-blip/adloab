"""واجهة سطر الأوامر: فحص واحد لمرة واحدة (مثالي لـ cron / GitHub Actions).

أمثلة:
    python -m app.cli check            # فحص كل الأهداف
    python -m app.cli check --json     # النتيجة بصيغة JSON
    python -m app.cli status           # ملخّص آخر 24 ساعة
    python -m app.cli domains          # النطاقات المسموح بفحصها
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from . import store as db
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
            f"{(stats['avg_ms'] or 0):<10} {stats['tls_days_left'] if stats['tls_days_left'] is not None else '-'}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="adloab-uptime", description="نظام مراقبة المواقع")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="فحص الأهداف مرة واحدة")
    check.add_argument("--json", action="store_true", help="إخراج JSON")
    sub.add_parser("status", help="ملخّص آخر 24 ساعة")
    sub.add_parser("domains", help="عرض النطاقات المسموح بفحصها")

    args = parser.parse_args(argv)
    if args.command == "check":
        return asyncio.run(_run_check(args.json))
    if args.command == "status":
        return _run_status()
    if args.command == "domains":
        print("\n".join(sorted(load_owned_domains())))
        return 0
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
