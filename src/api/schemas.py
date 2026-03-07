from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class PageCreate(BaseModel):
    url: str = Field(..., min_length=1)
    name: str | None = None
    viewport_width: int = Field(default=1920, ge=320, le=3840)
    viewport_height: int = Field(default=1080, ge=240, le=2160)
    check_interval_hours: int = Field(default=24, ge=1, le=720)
    diff_threshold: float = Field(default=0.5, ge=0.0, le=100.0)
    ignore_selectors: list[str] = Field(default_factory=list)
    wait_for_selector: str | None = None
    is_active: bool = True


class PageUpdate(BaseModel):
    url: str | None = None
    name: str | None = None
    viewport_width: int | None = Field(default=None, ge=320, le=3840)
    viewport_height: int | None = Field(default=None, ge=240, le=2160)
    check_interval_hours: int | None = Field(default=None, ge=1, le=720)
    diff_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    ignore_selectors: list[str] | None = None
    wait_for_selector: str | None = None
    is_active: bool | None = None


class PageResponse(BaseModel):
    id: str
    url: str
    name: str | None
    viewport_width: int
    viewport_height: int
    check_interval_hours: int
    diff_threshold: float
    ignore_selectors: list[str]
    wait_for_selector: str | None
    is_active: bool
    created_at: str
    updated_at: str


class SnapshotResponse(BaseModel):
    id: str
    page_id: str
    screenshot_path: str | None
    dom_hash: str | None
    diff_percent: float | None
    diff_image_path: str | None
    has_changes: bool | None
    error_message: str | None
    captured_at: str


class StatsResponse(BaseModel):
    total_pages: int
    active_pages: int
    last_snapshot_at: str | None
    last_check_at: str | None = None
    uptime_seconds: float | None = None


class CheckResponse(BaseModel):
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    last_run_at: str | None = None
    pages_checked: int = 0
    errors_count: int = 0
    uptime_seconds: float = 0
