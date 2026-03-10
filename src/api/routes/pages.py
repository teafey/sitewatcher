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

    try:
        if data.project_id:
            project = await db.get_project(data.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            page_data["project_id"] = project["id"]
        else:
            project = await db.resolve_project_for_url(data.url)
            page_data["project_id"] = project["id"]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # If viewports provided, serialize to dicts for JSONB and set compat fields
    if data.viewports:
        page_data["viewports"] = [v.model_dump() for v in data.viewports]
        # Keep viewport_width/viewport_height as first viewport for backward compat
        page_data["viewport_width"] = data.viewports[0].width
        page_data["viewport_height"] = data.viewports[0].height
    else:
        # Construct viewports from single viewport fields
        page_data["viewports"] = [{"width": data.viewport_width, "height": data.viewport_height}]

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

    try:
        if data.project_id:
            project = await db.get_project(data.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            update_data["project_id"] = project["id"]
        elif data.url:
            project = await db.resolve_project_for_url(data.url)
            update_data["project_id"] = project["id"]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Serialize viewports for JSONB and set compat fields
    if data.viewports:
        update_data["viewports"] = [v.model_dump() for v in data.viewports]
        update_data["viewport_width"] = data.viewports[0].width
        update_data["viewport_height"] = data.viewports[0].height

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
