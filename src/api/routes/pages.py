from __future__ import annotations

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
    await db.delete_page(page_id)
