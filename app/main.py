"""واجهة الويب: FastAPI + لوحة تحكم عربية (RTL) + API بسيط."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .checker import make_client, run_check
from .config import ROOT, NotOwnedError, load_targets
from .scheduler import check_all, loop

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("adloab")

STATIC_DIR = Path(__file__).parent / "static"
_state: dict = {"settings": None, "targets": []}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    settings, targets = load_targets()
    _state["settings"], _state["targets"] = settings, targets
    for target in targets:
        db.upsert_target(target.id, target.name, target.url, target.interval_seconds, target.enabled)
    log.info("تم تحميل %d هدف للمراقبة (concurrency=%d)", len(targets), settings.concurrency)

    stop = asyncio.Event()
    task = asyncio.create_task(loop(settings, targets, stop))
    try:
        yield
    finally:
        stop.set()
        task.cancel()


app = FastAPI(title="Adloab Uptime", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/api/status")
def status() -> dict:
    """حالة كل الأهداف + إحصاءات 24 ساعة."""
    targets = _state["targets"]
    latest = db.latest_checks([t.id for t in targets])
    payload = []
    for target in targets:
        stats = db.window_stats(target.id, hours=24)
        payload.append(
            {
                "id": target.id,
                "name": target.name,
                "url": target.url,
                "interval_seconds": target.interval_seconds,
                "enabled": target.enabled,
                "browser_check": target.browser_check,
                "latest": latest.get(target.id),
                "stats": stats,
            }
        )
    return {
        "targets": payload,
        "incidents_open": db.incidents(limit=10, only_open=True),
        "settings": {
            "concurrency": _state["settings"].concurrency,
            "timeout_seconds": _state["settings"].timeout_seconds,
            "failure_threshold": _state["settings"].failure_threshold,
            "alerts_enabled": _state["settings"].alerts_enabled,
        },
    }


@app.get("/api/targets/{target_id}/checks")
def target_checks(target_id: str, limit: int = Query(60, ge=1, le=500)) -> dict:
    rows = db.recent_checks(target_id, limit=limit)
    rows.reverse()  # من الأقدم إلى الأحدث لرسم المخطط
    return {"target_id": target_id, "checks": rows}


@app.get("/api/incidents")
def incidents(limit: int = Query(30, ge=1, le=200)) -> dict:
    return {"incidents": db.incidents(limit=limit)}


@app.post("/api/targets/{target_id}/check")
async def trigger_check(target_id: str) -> dict:
    """تشغيل فحص فوري لهدف واحد (زر «افحص الآن» في اللوحة)."""
    target = next((t for t in _state["targets"] if t.id == target_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="الهدف غير موجود")
    settings = _state["settings"]
    try:
        async with make_client(settings) as client:
            result = await run_check(client, target, settings)
    except NotOwnedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    db.insert_check(target.id, result)
    if result["ok"]:
        db.resolve_incidents(target.id)
    else:
        db.open_incident(target.id, result.get("reason") or "")
    return {"result": result}


@app.post("/api/check-all")
async def trigger_check_all() -> dict:
    results = await check_all(_state["settings"], _state["targets"])
    return {"count": len(results), "ok": sum(1 for r in results if r.get("ok"))}


@app.get("/api/config/domains")
def owned_domains() -> dict:
    """قائمة النطاقات المسموح بفحصها — شفافية كاملة حول حاجز الملكية."""
    from .config import load_owned_domains

    return {"owned_domains": sorted(load_owned_domains())}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:  # pragma: no cover - نقطة تشغيل
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
