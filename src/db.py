from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx

from src.project_utils import extract_hostname, normalize_base_url
from src.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "apikey": settings.supabase_key,
    "Authorization": f"Bearer {settings.supabase_key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

BASE_URL = f"{settings.supabase_url}/rest/v1"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=HEADERS, timeout=30.0)


# ── Pages ──────────────────────────────────────────────


async def get_active_pages() -> list[dict[str, Any]]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/pages",
            params={"is_active": "eq.true", "order": "created_at.asc"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_all_pages() -> list[dict[str, Any]]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/pages",
            params={"order": "created_at.desc"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_project_pages(project_id: str | UUID) -> list[dict[str, Any]]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/pages",
            params={
                "project_id": f"eq.{project_id}",
                "order": "created_at.desc",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_page(page_id: str | UUID) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/pages",
            params={"id": f"eq.{page_id}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def create_page(page_data: dict[str, Any]) -> dict[str, Any]:
    async with _client() as client:
        resp = await client.post(f"{BASE_URL}/pages", json=page_data)
        resp.raise_for_status()
        return resp.json()[0]


async def update_page(page_id: str | UUID, page_data: dict[str, Any]) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.patch(
            f"{BASE_URL}/pages",
            params={"id": f"eq.{page_id}"},
            json=page_data,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def delete_page(page_id: str | UUID) -> bool:
    async with _client() as client:
        resp = await client.delete(
            f"{BASE_URL}/pages",
            params={"id": f"eq.{page_id}"},
        )
        resp.raise_for_status()
        return True


# ── Projects ───────────────────────────────────────────


async def get_all_projects() -> list[dict[str, Any]]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/projects",
            params={"order": "created_at.desc"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_project(project_id: str | UUID) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/projects",
            params={"id": f"eq.{project_id}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def get_project_by_hostname(hostname: str) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/projects",
            params={"hostname": f"eq.{hostname}", "limit": "1"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def create_project(project_data: dict[str, Any]) -> dict[str, Any]:
    async with _client() as client:
        resp = await client.post(f"{BASE_URL}/projects", json=project_data)
        resp.raise_for_status()
        return resp.json()[0]


async def update_project(project_id: str | UUID, project_data: dict[str, Any]) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.patch(
            f"{BASE_URL}/projects",
            params={"id": f"eq.{project_id}"},
            json=project_data,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def resolve_project_for_url(url: str) -> dict[str, Any]:
    hostname = extract_hostname(url)
    existing = await get_project_by_hostname(hostname)
    if existing:
        return existing
    return await create_project(
        {
            "name": hostname,
            "base_url": normalize_base_url(url),
            "hostname": hostname,
        }
    )


async def prepare_project_payload(name: str, base_url: str) -> dict[str, str]:
    hostname = extract_hostname(base_url)
    return {
        "name": name.strip(),
        "base_url": normalize_base_url(base_url),
        "hostname": hostname,
    }


async def get_project_rows() -> list[dict[str, Any]]:
    projects = await get_all_projects()
    pages = await _get_pages_minimal()
    latest_snapshots, _ = await _get_latest_snapshot_map()

    counts_by_project: dict[str, int] = {}
    attention_by_project: dict[str, int] = {}

    for page in pages:
        project_id = page.get("project_id")
        if not project_id:
            continue
        counts_by_project[project_id] = counts_by_project.get(project_id, 0) + 1

        latest = latest_snapshots.get(page["id"])
        needs_attention = bool(
            page.get("is_active")
            and latest
            and (latest.get("has_changes") or latest.get("error_message"))
        )
        if needs_attention:
            attention_by_project[project_id] = attention_by_project.get(project_id, 0) + 1

    return [
        {
            **project,
            "pages_count": counts_by_project.get(project["id"], 0),
            "attention_count": attention_by_project.get(project["id"], 0),
        }
        for project in projects
    ]


# ── Snapshots ──────────────────────────────────────────


async def create_snapshot(snapshot_data: dict[str, Any]) -> dict[str, Any]:
    async with _client() as client:
        resp = await client.post(f"{BASE_URL}/snapshots", json=snapshot_data)
        resp.raise_for_status()
        return resp.json()[0]


async def get_latest_snapshot(
    page_id: str | UUID,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
) -> dict[str, Any] | None:
    params: dict[str, str] = {
        "page_id": f"eq.{page_id}",
        "order": "captured_at.desc",
        "limit": "1",
    }
    if viewport_width is not None:
        params["viewport_width"] = f"eq.{viewport_width}"
    if viewport_height is not None:
        params["viewport_height"] = f"eq.{viewport_height}"
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/snapshots",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def get_snapshots(
    page_id: str | UUID,
    limit: int = 20,
    offset: int = 0,
    changes_only: bool = False,
    viewport_width: int | None = None,
    viewport_height: int | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "page_id": f"eq.{page_id}",
        "order": "captured_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    if changes_only:
        params["has_changes"] = "eq.true"
    if viewport_width is not None:
        params["viewport_width"] = f"eq.{viewport_width}"
    if viewport_height is not None:
        params["viewport_height"] = f"eq.{viewport_height}"
    async with _client() as client:
        resp = await client.get(f"{BASE_URL}/snapshots", params=params)
        resp.raise_for_status()
        return resp.json()


async def get_snapshot(snapshot_id: str | UUID) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/snapshots",
            params={"id": f"eq.{snapshot_id}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def delete_snapshot(snapshot_id: str | UUID) -> bool:
    async with _client() as client:
        resp = await client.delete(
            f"{BASE_URL}/snapshots",
            params={"id": f"eq.{snapshot_id}"},
        )
        resp.raise_for_status()
        return True


async def get_snapshots_count(page_id: str | UUID, changes_only: bool = False) -> int:
    params: dict[str, str] = {
        "page_id": f"eq.{page_id}",
        "select": "id",
    }
    if changes_only:
        params["has_changes"] = "eq.true"
    headers = {**HEADERS, "Prefer": "count=exact"}
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/snapshots",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        content_range = resp.headers.get("content-range", "*/0")
        total = content_range.split("/")[-1]
        return int(total) if total != "*" else 0


async def get_stats() -> dict[str, Any]:
    pages = await _get_pages_minimal()
    projects = await get_all_projects()
    latest_snapshots, last_snapshot_at = await _get_latest_snapshot_map()

    active_pages = sum(1 for page in pages if page.get("is_active"))
    attention_pages = sum(
        1
        for page in pages
        if page.get("is_active")
        and (
            latest_snapshots.get(page["id"], {}).get("has_changes")
            or latest_snapshots.get(page["id"], {}).get("error_message")
        )
    )

    return {
        "total_projects": len(projects),
        "total_pages": len(pages),
        "active_pages": active_pages,
        "attention_pages": attention_pages,
        "last_snapshot_at": last_snapshot_at,
    }


async def _get_pages_minimal() -> list[dict[str, Any]]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/pages",
            params={"select": "id,project_id,is_active"},
        )
        resp.raise_for_status()
        return resp.json()


async def _get_latest_snapshot_map() -> tuple[dict[str, dict[str, Any]], str | None]:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/snapshots",
            params={
                "select": "page_id,has_changes,error_message,captured_at",
                "order": "captured_at.desc",
            },
        )
        resp.raise_for_status()
        snapshots = resp.json()

    latest_by_page: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        page_id = snapshot["page_id"]
        if page_id not in latest_by_page:
            latest_by_page[page_id] = snapshot

    last_snapshot_at = snapshots[0]["captured_at"] if snapshots else None
    return latest_by_page, last_snapshot_at
