from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx

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


# ── Snapshots ──────────────────────────────────────────


async def create_snapshot(snapshot_data: dict[str, Any]) -> dict[str, Any]:
    async with _client() as client:
        resp = await client.post(f"{BASE_URL}/snapshots", json=snapshot_data)
        resp.raise_for_status()
        return resp.json()[0]


async def get_latest_snapshot(page_id: str | UUID) -> dict[str, Any] | None:
    async with _client() as client:
        resp = await client.get(
            f"{BASE_URL}/snapshots",
            params={
                "page_id": f"eq.{page_id}",
                "order": "captured_at.desc",
                "limit": "1",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None


async def get_snapshots(
    page_id: str | UUID,
    limit: int = 20,
    offset: int = 0,
    changes_only: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "page_id": f"eq.{page_id}",
        "order": "captured_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    if changes_only:
        params["has_changes"] = "eq.true"
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
    async with _client() as client:
        pages_resp = await client.get(
            f"{BASE_URL}/pages",
            params={"select": "id,is_active"},
        )
        pages_resp.raise_for_status()
        pages = pages_resp.json()

        total_pages = len(pages)
        active_pages = sum(1 for p in pages if p.get("is_active"))

        snapshots_resp = await client.get(
            f"{BASE_URL}/snapshots",
            params={"order": "captured_at.desc", "limit": "1"},
        )
        snapshots_resp.raise_for_status()
        latest = snapshots_resp.json()

        return {
            "total_pages": total_pages,
            "active_pages": active_pages,
            "last_snapshot_at": latest[0]["captured_at"] if latest else None,
        }
