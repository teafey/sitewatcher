from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes.pages import router as pages_router
from src.api.routes.snapshots import router as snapshots_router, stats_router
from src.api.schemas import CheckResponse, HealthResponse
from src.config import settings

logger = logging.getLogger(__name__)

# Global state for health tracking
app_state: dict[str, Any] = {
    "start_time": time.time(),
    "last_run_at": None,
    "last_results": None,
    "check_running": False,
}

scheduler = AsyncIOScheduler()


async def scheduled_check() -> None:
    if app_state["check_running"]:
        logger.warning("Check cycle already running, skipping")
        return

    app_state["check_running"] = True
    try:
        from src.pipeline import run_check_cycle
        results = await run_check_cycle()
        app_state["last_run_at"] = datetime.now(timezone.utc).isoformat()
        app_state["last_results"] = results
    except Exception as exc:
        logger.error("Scheduled check failed: %s", exc)
    finally:
        app_state["check_running"] = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler
    scheduler.add_job(
        scheduled_check,
        "interval",
        hours=settings.check_interval_hours,
        id="check_cycle",
        replace_existing=True,
    )
    # Retention cleanup — run daily
    async def retention_job():
        from src.retention import cleanup_old_snapshots
        try:
            await cleanup_old_snapshots()
        except Exception as exc:
            logger.error("Retention cleanup failed: %s", exc)

    scheduler.add_job(
        retention_job,
        "interval",
        hours=24,
        id="retention_cleanup",
        replace_existing=True,
    )

    # Self-monitoring — check if cycle was missed
    async def self_monitor():
        from datetime import datetime, timezone
        last_run = app_state.get("last_run_at")
        if last_run:
            from datetime import datetime, timezone
            last_dt = datetime.fromisoformat(last_run)
            now = datetime.now(timezone.utc)
            hours_since = (now - last_dt).total_seconds() / 3600
            max_gap = settings.check_interval_hours * 2
            if hours_since > max_gap:
                logger.warning("Check cycle missed! Last run: %s (%.1fh ago)", last_run, hours_since)
                # Send alert via configured notifiers
                from src.notify import get_notifiers
                for notifier in get_notifiers():
                    try:
                        await notifier.send_change_alert(
                            {"id": "system", "url": "system", "name": "SiteWatcher System"},
                            {
                                "id": "system",
                                "diff_percent": 0,
                                "captured_at": now.isoformat(),
                                "text_diff": f"Check cycle missed! Last run was {hours_since:.1f}h ago.",
                            },
                        )
                    except Exception:
                        pass

    scheduler.add_job(
        self_monitor,
        "interval",
        hours=1,
        id="self_monitor",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started (interval: %dh)", settings.check_interval_hours)

    # Ensure data directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="SiteWatcher API",
    description="Visual web page change monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key authentication middleware
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Skip auth for health endpoint and static files
    path = request.url.path
    if path in ("/api/health", "/docs", "/openapi.json") or path.startswith("/static"):
        return await call_next(request)

    if settings.api_key:
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")

    return await call_next(request)


# Mount static files for data directory
app.mount("/static/data", StaticFiles(directory=str(settings.data_dir)), name="data")

# Include routers
app.include_router(pages_router)
app.include_router(snapshots_router)
app.include_router(stats_router)


@app.post("/api/check", response_model=CheckResponse)
async def trigger_check():
    if app_state["check_running"]:
        return CheckResponse(status="already_running", message="Check cycle is already running")

    asyncio.create_task(scheduled_check())
    return CheckResponse(status="started", message="Check cycle started")


@app.post("/api/check/{page_id}", response_model=CheckResponse)
async def trigger_check_page(page_id: str):
    from src.pipeline import check_single_page

    async def _run():
        try:
            await check_single_page(page_id)
        except Exception as exc:
            logger.error("Single page check failed: %s", exc)

    asyncio.create_task(_run())
    return CheckResponse(status="started", message=f"Check started for page {page_id}")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    uptime = time.time() - app_state["start_time"]
    results = app_state.get("last_results") or {}
    return HealthResponse(
        status="healthy",
        last_run_at=app_state.get("last_run_at"),
        pages_checked=results.get("checked", 0),
        errors_count=results.get("errors", 0),
        uptime_seconds=round(uptime, 1),
    )
