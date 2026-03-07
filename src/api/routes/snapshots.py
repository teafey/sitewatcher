from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from src import db
from src.api.schemas import SnapshotResponse, StatsResponse

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("/{page_id}", response_model=list[SnapshotResponse])
async def list_snapshots(
    page_id: str,
    limit: int = 20,
    offset: int = 0,
    changes_only: bool = False,
):
    page = await db.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    snapshots = await db.get_snapshots(
        page_id, limit=limit, offset=offset, changes_only=changes_only,
    )
    return snapshots


@router.get("/detail/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(snapshot_id: str):
    snapshot = await db.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot


@router.get("/detail/{snapshot_id}/screenshot")
async def get_screenshot(snapshot_id: str):
    snapshot = await db.get_snapshot(snapshot_id)
    if not snapshot or not snapshot.get("screenshot_path"):
        raise HTTPException(status_code=404, detail="Screenshot not found")

    path = Path(snapshot["screenshot_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")

    return FileResponse(path, media_type="image/png")


@router.get("/detail/{snapshot_id}/diff-image")
async def get_diff_image(snapshot_id: str):
    snapshot = await db.get_snapshot(snapshot_id)
    if not snapshot or not snapshot.get("diff_image_path"):
        raise HTTPException(status_code=404, detail="Diff image not found")

    path = Path(snapshot["diff_image_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Diff image file not found")

    return FileResponse(path, media_type="image/png")


@router.get("/detail/{snapshot_id}/text-diff")
async def get_text_diff(snapshot_id: str):
    snapshot = await db.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    text_diff = snapshot.get("text_diff") or ""
    return PlainTextResponse(text_diff)


stats_router = APIRouter(tags=["stats"])


@stats_router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    stats = await db.get_stats()
    return stats
