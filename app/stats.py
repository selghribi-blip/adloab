"""حسابات مشتركة بين خلفيات التخزين (SQLite وPostgres)."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


def percentile(values: list[float], pct: float) -> float | None:
    """النسبة المئوية المطلوبة (تقريب بسيط بلا مكتبات إضافية)."""
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100) * (len(ordered) - 1))))
    return round(ordered[index], 1)


def window_stats_from_rows(rows: Iterable[Mapping[str, Any]], hours: int) -> dict[str, Any]:
    """إحصاءات نافذة زمنية من صفوف الفحوصات (تشترك فيها كل الخلفيات)."""
    rows = list(rows)
    total = len(rows)
    ok_rows = [r for r in rows if r.get("ok")]
    latencies = [float(r["total_ms"]) for r in ok_rows if r.get("total_ms") is not None]
    tls_values = [float(r["tls_days_left"]) for r in ok_rows if r.get("tls_days_left") is not None]

    return {
        "checks": total,
        "uptime_pct": round(100 * len(ok_rows) / total, 2) if total else None,
        "avg_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "max_ms": round(max(latencies), 1) if latencies else None,
        "tls_days_left": min(tls_values) if tls_values else None,
        "window_hours": hours,
    }
