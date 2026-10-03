#!/usr/bin/env python3
"""بديل بلا تثبيت لـ k6: مولّد حمل مكتوب بـ asyncio — يعمل بأمر واحد وأي مكان.

    python loadtest/py_load.py --url http://127.0.0.1:8000/healthz \
        --vus 20 --duration 30 --i-own-this-site

المقاييس: معدّل الطلبات/ثانية، متوسط/وسيط/p95/p99 زمن الاستجابة، نسبة الأخطاء.
حدود القبول (قابلة للتغيير): p95 < 500ms و نسبة الأخطاء < 1%.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import NotOwnedError, assert_allowed, load_owned_domains  # noqa: E402


class Results:
    def __init__(self) -> None:
        self.latencies: list[float] = []
        self.statuses: list[int] = []
        self.errors: list[str] = []
        self.lock = asyncio.Lock()

    async def record(self, latency_ms: float | None, status: int | None, error: str | None) -> None:
        async with self.lock:
            if latency_ms is not None:
                self.latencies.append(latency_ms)
            if status is not None:
                self.statuses.append(status)
            if error:
                self.errors.append(error)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


async def worker(
    client: httpx.AsyncClient, url: str, results: Results, deadline: float, think_time: float
) -> None:
    """مستخدم وهمي واحد: طلبات متتالية بإيقاع شبه بشري حتى نهاية المدة."""
    while time.perf_counter() < deadline:
        started = time.perf_counter()
        try:
            response = await client.get(url)
            latency = (time.perf_counter() - started) * 1000
            await results.record(latency, response.status_code, None)
        except Exception as exc:  # noqa: BLE001
            await results.record(None, None, f"{type(exc).__name__}: {exc}")
        if think_time:
            await asyncio.sleep(think_time)


async def run(args: argparse.Namespace) -> int:
    start = time.perf_counter()
    deadline = start + args.duration
    results = Results()

    limits = httpx.Limits(max_connections=args.vus * 2, max_keepalive_connections=args.vus)
    timeout = httpx.Timeout(args.timeout)

    print(f"🎯 {args.url}")
    print(f"👥 {args.vus} مستخدم وهمي · ⏱️  {args.duration} ثانية · 🧠 زمن تفكير {args.think_time}s")
    print("▶️  جارٍ التوليد ... (نتجاهل أول 3 ثوانٍ كإحماء)")

    async with httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "AdloabLoadTest/1.0 (authorized load test)"},
    ) as client:
        # مرحلة إحماء قصيرة: تُهيّئ الاتصالات وتُسخّن المسار بلا احتساب نتائجها
        warmup_deadline = min(start + 3, deadline)
        await asyncio.gather(
            *(worker(client, args.url, Results(), warmup_deadline, 0) for _ in range(args.vus))
        )
        measured_start = time.perf_counter()
        measured_deadline = measured_start + args.duration
        await asyncio.gather(
            *(
                worker(client, args.url, results, measured_deadline, args.think_time)
                for _ in range(args.vus)
            )
        )
        elapsed = time.perf_counter() - measured_start
    total = len(results.latencies) + len(results.errors)
    ok = len(results.statuses)
    failed_requests = sum(1 for s in results.statuses if s >= 500) + len(results.errors)
    error_rate = (failed_requests / total * 100) if total else 0.0
    rps = total / elapsed if elapsed else 0

    p95 = percentile(results.latencies, 95)
    p99 = percentile(results.latencies, 99)

    print("\n" + "=" * 58)
    print("  ملخّص اختبار الحمل (asyncio)")
    print("=" * 58)
    print(f"  المدة الفعلية        : {round(elapsed, 1)} ثانية")
    print(f"  إجمالي الطلبات      : {total}")
    print(f"  معدّل الطلبات       : {round(rps, 1)} طلب/ثانية")
    print(f"  ردود ناجحة          : {ok}")
    print(f"  نسبة الأخطاء        : {round(error_rate, 2)}%")
    if results.latencies:
        print(f"  متوسط الزمن         : {round(statistics.fmean(results.latencies), 1)} ms")
        print(f"  الوسيط              : {round(statistics.median(results.latencies), 1)} ms")
        print(f"  الذروة p95          : {round(p95, 1)} ms")
        print(f"  الذروة p99          : {round(p99, 1)} ms")
        print(f"  أبطأ طلب            : {round(max(results.latencies), 1)} ms")
    if results.statuses:
        unique = sorted(set(results.statuses))
        print(f"  رموز الحالة         : {', '.join(str(s) for s in unique)}")
    if results.errors:
        print(f"  أول خطأ             : {results.errors[0][:90]}")
    print("=" * 58)

    breaches = []
    if p95 > args.max_p95:
        breaches.append(f"p95 = {round(p95, 1)}ms > الحد {args.max_p95}ms")
    if error_rate > args.max_error_rate:
        breaches.append(f"نسبة الأخطاء = {round(error_rate, 2)}% > الحد {args.max_error_rate}%")

    if breaches:
        print("⚠️  تجاوز الحدود: " + " · ".join(breaches))
        print("   → راجع قاعدة البيانات أو أضف تخزينًا مؤقتًا أو ارفع عدد العمال (workers).")
        return 1
    print("✅ كل الحدود محترمة — الأداء مقبول تحت هذا الحمل.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="مولّد حمل بسيط (بديل k6) لمواقعك فقط")
    parser.add_argument("--url", required=True, help="الرابط المستهدف")
    parser.add_argument("--vus", type=int, default=20, help="عدد المستخدمين الوهميين")
    parser.add_argument("--duration", type=float, default=30, help="مدة الاختبار بالثواني")
    parser.add_argument("--think-time", type=float, default=0.0, help="انتظار بين الطلبات (ثوانٍ)")
    parser.add_argument("--timeout", type=float, default=10.0, help="مهلة الطلب")
    parser.add_argument("--max-p95", type=float, default=500.0, help="حد p95 بالمللي ثانية")
    parser.add_argument("--max-error-rate", type=float, default=1.0, help="حد نسبة الأخطاء %")
    parser.add_argument(
        "--i-own-this-site", action="store_true", dest="confirmed", help="تأكيد الملكية أو الإذن"
    )
    args = parser.parse_args(argv)

    try:
        assert_allowed(args.url)
    except NotOwnedError as exc:
        print(f"\n🚫 {exc}\n")
        print("النطاقات المسموح بها حاليًا: " + ", ".join(sorted(load_owned_domains())))
        print("\nاختبار الحمل على موقع لا تملكه = هجوم حجب خدمة (DoS).")
        return 2

    if not args.confirmed:
        print("\n🔒 أكّد الملكية أو الإذن الكتابي: --i-own-this-site")
        return 3

    if args.vus < 1 or args.duration < 3:
        print("⚠️  استخدم --vus >= 1 و --duration >= 3")
        return 64

    print(f"🌐 النطاق: {urlparse(args.url).hostname} (مرخّص)")
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
