from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src import db
from src.api.schemas import PageCreate, PageUpdate, PageResponse

router = APIRouter(prefix="/api/pages", tags=["pages"])


@router.get("", response_model=list[PageResponse])
async def list_pages():
    pages = await db.get_all_pages()
    return pages


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(page_id: str):
    page = await db.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("", response_model=PageResponse, status_code=201)
async def create_page(data: PageCreate, background_tasks: BackgroundTasks):
    page_data = data.model_dump(exclude_none=True)
    page = await db.create_page(page_data)

    # Trigger baseline capture in background
    from src.pipeline import check_single_page
    background_tasks.add_task(check_single_page, page["id"])

    return page


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(page_id: str, data: PageUpdate):
    existing = await db.get_page(page_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")

    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        return existing

    updated = await db.update_page(page_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Page not found")
    return updated


@router.delete("/{page_id}", status_code=204)
async def delete_page(page_id: str):
    existing = await db.get_page(page_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Page not found")

    # Delete snapshot files from disk before cascade removes DB records
    snapshots = await db.get_snapshots(page_id, limit=10000)
    for snap in snapshots:
        for path_key in ("screenshot_path", "diff_image_path"):
            path_str = snap.get(path_key)
            if path_str:
                parent = Path(path_str).parent
                if parent.exists():
                    shutil.rmtree(parent, ignore_errors=True)

    await db.delete_page(page_id)
