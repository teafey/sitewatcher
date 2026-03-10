from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src import db
from src.api.schemas import (
    PageResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectRowResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRowResponse])
async def list_projects():
    return await db.get_project_rows()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/pages", response_model=list[PageResponse])
async def get_project_pages(project_id: str):
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await db.get_project_pages(project_id)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate):
    try:
        project_data = await db.prepare_project_payload(data.name, str(data.base_url))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    existing = await db.get_project_by_hostname(project_data["hostname"])
    if existing:
        raise HTTPException(status_code=409, detail="Project already exists for this hostname")
    return await db.create_project(project_data)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, data: ProjectUpdate):
    existing = await db.get_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name.strip()
    if data.base_url is not None:
        try:
            normalized = await db.prepare_project_payload(
                update_data.get("name", existing["name"]),
                str(data.base_url),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        conflicting = await db.get_project_by_hostname(normalized["hostname"])
        if conflicting and conflicting["id"] != project_id:
            raise HTTPException(status_code=409, detail="Project already exists for this hostname")
        update_data["base_url"] = normalized["base_url"]
        update_data["hostname"] = normalized["hostname"]

    if not update_data:
        return existing

    updated = await db.update_project(project_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated
