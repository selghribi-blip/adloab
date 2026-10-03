#!/usr/bin/env python3
"""مُشغّل اختبار الحمل — مع حاجز الملكية نفسه المستخدم في المراقبة.

لا يعمل إلا على نطاق موجود في config/owned_domains.yaml (موقعك أو نسخة staging).
يحاول أولًا إيجاد k6 في PATH، وإن لم يجده يحاول تنزيله من إصدارات GitHub في
مجلد .k6/ (غير مُتتبَّع في git)، وإن فشل كل ذلك يرشدك إلى loadtest/py_load.py.

أمثلة:
    python loadtest/run.py --target "mysite.ma" --scenario smoke --i-own-this-site
    python loadtest/run.py --url https://staging.mysite.ma --scenario load --vus 30 --i-own-this-site
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import NotOwnedError, assert_allowed, load_owned_domains  # noqa: E402

K6_DIR = ROOT / ".k6"
K6_SCRIPTS = ROOT / "loadtest" / "k6"
RELEASES_API = "https://api.github.com/repos/grafana/k6/releases/latest"


def resolve_url(args: argparse.Namespace) -> str:
    if args.url:
        return args.url
    if args.target:
        import yaml

        raw = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text(encoding="utf-8")) or {}
        for item in raw.get("targets") or []:
            name = str(item.get("name", ""))
            url = str(item.get("url", ""))
            if args.target.lower() in (name.lower(), urlparse(url).hostname or ""):
                return url
        raise SystemExit(f"❌ لم أجد هدفًا مطابقًا لـ «{args.target}» في config/targets.yaml")
    return "http://127.0.0.1:8000/healthz"  # الفحص الذاتي المحلي


def guard(url: str) -> None:
    """حاجز الملكية: يوقف التنفيذ إن لم يكن النطاق مصرّحًا به."""
    try:
        assert_allowed(url)
    except NotOwnedError as exc:
        print(f"\n🚫 {exc}\n")
        print("النطاقات المسموح بها حاليًا:")
        for domain in sorted(load_owned_domains()):
            print(f"   - {domain}")
        print(
            "\nاختبار الحمل على موقع لا تملكه = هجوم حجب خدمة (DoS)، وهو جريمة في معظم الدول\n"
            "ويخالف شروط استخدام كل مزوّدي الاستضافة."
        )
        raise SystemExit(2) from exc


def find_k6() -> str | None:
    found = shutil.which("k6")
    if found:
        return found
    local = K6_DIR / "k6"
    if local.exists():
        return str(local)
    return None


def download_k6() -> str | None:
    """تنزيل k6 من إصدارات GitHub (يعمل على جهازك وفي CI، وقد يُحجب في بيئات مقيّدة)."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_part = "linux" if system == "linux" else ("darwin" if system == "darwin" else None)
    arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
    if os_part is None:
        return None

    print("⬇️  محاولة تنزيل k6 ...")
    try:
        with urllib.request.urlopen(RELEASES_API, timeout=20) as response:
            release = json.load(response)
        wanted = f"k6-{release['tag_name']}-{os_part}-{arch}.tar.gz"
        asset = next((a for a in release["assets"] if a["name"] == wanted), None)
        if asset is None:
            print(f"⚠️  لم أجد الحزمة {wanted}")
            return None

        K6_DIR.mkdir(exist_ok=True)
        archive = K6_DIR / wanted
        urllib.request.urlretrieve(asset["browser_download_url"], archive)
        with tarfile.open(archive) as tar:
            member = next(m for m in tar.getmembers() if m.name.endswith("/k6") or m.name == "k6")
            member.name = "k6"
            tar.extract(member, K6_DIR)
        (K6_DIR / "k6").chmod(0o755)
        return str(K6_DIR / "k6")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  تعذّر تنزيل k6: {type(exc).__name__}: {exc}")
        print("   استخدم البديل الجاهز بلا تثبيت:  python loadtest/py_load.py --url <رابطك>")
        return None


def _metric_values(metric: dict) -> dict:
    """قيم المقياس: في k6 الحديث تكون مسطّحة، وفي القديم داخل values."""
    nested = metric.get("values")
    if isinstance(nested, dict):
        return nested
    return {k: v for k, v in metric.items() if k not in ("thresholds", "type", "contains")}


def _breached_thresholds(metric: dict) -> list[str]:
    """أسماء الحدود المتجاوَزة — متوافق مع الصيغتين:
    الحديثة: {"p(95)<500": true}  حيث true = متجاوَز
    القديمة: {"p(95)<500": {"ok": true}} حيث true = محترم
    """
    result = []
    for expression, status in (metric.get("thresholds") or {}).items():
        if isinstance(status, bool):
            breached = status
        else:
            breached = not status.get("ok", True)
        if breached:
            result.append(expression)
    return result


def print_summary(summary_path: Path, k6_exit_code: int) -> int:
    """طباعة ملخّص عربي من ملف summary-export، وإرجاع كود الخروج النهائي."""
    if not summary_path.exists():
        if k6_exit_code != 0:
            print(f"❌ فشل تشغيل k6 (كود {k6_exit_code}) — راجع الرسائل أعلاه.")
        return k6_exit_code
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})

    duration = _metric_values(metrics.get("http_req_duration", {}))
    reqs_values = _metric_values(metrics.get("http_reqs", {}))
    failed_values = _metric_values(metrics.get("http_req_failed", {}))
    checks_values = _metric_values(metrics.get("checks", {}))

    count = reqs_values.get("count")
    rps = reqs_values.get("rate")
    # في صيغة k6 الحديثة قيمة المقاييس النسبية في "value"، وفي القديمة في "rate"
    failed_rate = failed_values.get("rate", failed_values.get("value"))
    checks_rate = checks_values.get("rate", checks_values.get("value"))

    def ms(key: str) -> str:
        # قيم k6 الزمنية في ملف الملخّص بالمللي ثانية أصلًا
        value = duration.get(key)
        return f"{round(value, 1)} ms" if isinstance(value, (int, float)) else "—"

    print("\n" + "=" * 58)
    print("  ملخّص اختبار الحمل (k6)")
    print("=" * 58)
    print(f"  إجمالي الطلبات      : {int(count) if count else '—'}")
    print(f"  معدّل الطلبات       : {round(rps, 1) if rps else '—'} طلب/ثانية")
    print(f"  متوسط الزمن         : {ms('avg')}")
    print(f"  الوسيط (med)        : {ms('med')}")
    print(f"  الذروة p95          : {ms('p(95)')}")
    print(f"  الذروة p99          : {ms('p(99)')}")
    print(f"  أبطأ طلب            : {ms('max')}")
    if failed_rate is not None:
        print(f"  نسبة الأخطاء        : {round(failed_rate * 100, 2)}%")
    if checks_rate is not None:
        print(f"  نجاح الفحوصات       : {round(checks_rate * 100, 2)}%")
    print("=" * 58)

    breached: list[str] = []
    for metric in metrics.values():
        breached.extend(_breached_thresholds(metric))

    if breached:
        print("⚠️  حدود لم تُحترم: " + ", ".join(sorted(set(breached))))
        print("   → السيرفر يحتاج تحسينًا قبل الإطلاق (انظر p95 ونسبة الأخطاء أعلاه).")
        return 1
    if k6_exit_code != 0:
        print(f"⚠️  خرج k6 بكود {k6_exit_code} — راجع التفاصيل أعلاه.")
        return k6_exit_code

    print("✅ كل الحدود محترمة — الأداء مقبول تحت هذا الحمل.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="اختبار حمل لمقال تملكه فقط")
    parser.add_argument("--url", help="الرابط الكامل المستهدف")
    parser.add_argument("--target", help="اسم هدف من config/targets.yaml أو نطاقه")
    parser.add_argument(
        "--scenario", choices=["smoke", "load", "stress"], default="smoke", help="نوع السيناريو"
    )
    parser.add_argument("--vus", type=int, default=20, help="عدد المستخدمين الوهميين (load)")
    parser.add_argument("--duration", default="1m", help="مدة الثبات (load)")
    parser.add_argument("--path", default="/healthz", help="المسار المفحوص")
    parser.add_argument(
        "--i-own-this-site",
        action="store_true",
        dest="confirmed",
        help="تأكيد أنك تملك الموقع أو لديك إذن كتابي باختباره",
    )
    parser.add_argument("--install-k6", action="store_true", help="تنزيل k6 إن لم يكن موجودًا")
    args = parser.parse_args(argv)

    url = resolve_url(args)
    print(f"🎯 الهدف: {url}")
    guard(url)

    if not args.confirmed:
        print(
            "\n🔒 اختبار الحمل يولّد ضغطًا حقيقيًا على الخدمة. أكّد الملكية أو الإذن:\n"
            "   --i-own-this-site\n"
            "   ولا تشغّل سيناريو stress على الإنتاج — استخدم نسخة staging."
        )
        return 3

    k6 = find_k6() or (download_k6() if args.install_k6 else None)
    if k6 is None:
        print(
            "\nℹ️  k6 غير مثبّت. الخيارات:\n"
            "   1) python loadtest/run.py ... --install-k6\n"
            "   2) بديل بلا تثبيت:  python loadtest/py_load.py --url "
            f"{url} --vus {args.vus} --duration {args.duration} --i-own-this-site\n"
            "   3) تثبيت يدوي: https://grafana.com/docs/k6/latest/set-up/install-k6/"
        )
        return 4

    summary_path = ROOT / ".k6" / "summary.json"
    summary_path.parent.mkdir(exist_ok=True)
    summary_path.unlink(missing_ok=True)  # لا نقرأ ملخّصًا قديمًا إذا فشل التشغيل
    env = {
        **os.environ,
        "BASE_URL": url.rsplit("/", 1)[0] if args.path not in url else url,
        "TARGET_PATH": args.path,
        "VUS": str(args.vus),
        "DURATION": args.duration,
    }
    # نبني BASE_URL وPATH بشكل صحيح: k6 يتوقع الأصل بدون المسار
    parsed = urlparse(url)
    env["BASE_URL"] = f"{parsed.scheme}://{parsed.netloc}"
    env["TARGET_PATH"] = parsed.path if parsed.path not in ("", "/") else args.path

    script = K6_SCRIPTS / f"{args.scenario}.js"
    command = [k6, "run", str(script), "--summary-export", str(summary_path)]
    print(f"▶️  تشغيل السيناريو «{args.scenario}» بوساطة k6 ...\n")
    result = subprocess.run(command, env=env, cwd=str(ROOT), check=False)

    code = print_summary(summary_path, result.returncode)
    if result.returncode != 0 and code == 0:
        return result.returncode
    return code


if __name__ == "__main__":
    sys.exit(main())
