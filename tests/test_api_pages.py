"""Tests for the FastAPI pages API.

These tests require a running Supabase instance.
Run with: pytest tests/test_api_pages.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Disable API key auth for testing
    with patch("src.config.settings") as mock_settings:
        mock_settings.api_key = ""
        mock_settings.data_dir.__str__ = lambda _: "/tmp/sitewatcher-test"
        mock_settings.check_interval_hours = 24
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = ""
        mock_settings.telegram_enabled = False
        mock_settings.bitrix_enabled = False

        from src.api.main import app
        yield TestClient(app)


class TestPagesAPI:
    @patch("src.db.get_all_pages", new_callable=AsyncMock)
    def test_list_pages(self, mock_get, client):
        mock_get.return_value = [
            {
                "id": "test-id",
                "url": "https://example.com",
                "name": "Test",
                "project_id": "project-id",
                "viewport_width": 1920,
                "viewport_height": 1080,
                "viewports": [{"width": 1920, "height": 1080}],
                "check_interval_hours": 24,
                "diff_threshold": 0.5,
                "ignore_selectors": [],
                "wait_for_selector": None,
                "scroll_to_bottom": True,
                "max_scrolls": 10,
                "wait_seconds": 3,
                "is_active": True,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]
        resp = client.get("/api/pages")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("src.db.get_page", new_callable=AsyncMock)
    def test_get_page_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/pages/nonexistent")
        assert resp.status_code == 404

    @patch("src.pipeline.check_single_page", new_callable=AsyncMock)
    @patch("src.db.create_page", new_callable=AsyncMock)
    @patch("src.db.resolve_project_for_url", new_callable=AsyncMock)
    def test_create_page(self, mock_resolve_project, mock_create, mock_check, client):
        mock_resolve_project.return_value = {
            "id": "project-id",
            "name": "example.com",
            "base_url": "https://example.com",
            "hostname": "example.com",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        mock_create.return_value = {
            "id": "new-id",
            "url": "https://example.com",
            "name": "New Page",
            "project_id": "project-id",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "viewports": [{"width": 1920, "height": 1080}],
            "check_interval_hours": 24,
            "diff_threshold": 0.5,
            "ignore_selectors": [],
            "wait_for_selector": None,
            "scroll_to_bottom": True,
            "max_scrolls": 10,
            "wait_seconds": 3,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        resp = client.post(
            "/api/pages",
            json={"url": "https://example.com", "name": "New Page"},
        )
        assert resp.status_code == 201
        assert resp.json()["project_id"] == "project-id"
        mock_create.assert_awaited_once()
        created_payload = mock_create.await_args.args[0]
        assert created_payload["project_id"] == "project-id"

    @patch("src.pipeline.check_single_page", new_callable=AsyncMock)
    @patch("src.db.create_page", new_callable=AsyncMock)
    @patch("src.db.get_project", new_callable=AsyncMock)
    def test_create_page_with_project_id(self, mock_get_project, mock_create, mock_check, client):
        mock_get_project.return_value = {
            "id": "project-id",
            "name": "Example",
            "base_url": "https://example.com",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        mock_create.return_value = {
            "id": "new-id",
            "url": "https://example.com/path",
            "name": "New Page",
            "project_id": "project-id",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "viewports": [{"width": 1920, "height": 1080}],
            "check_interval_hours": 24,
            "diff_threshold": 0.5,
            "ignore_selectors": [],
            "wait_for_selector": None,
            "scroll_to_bottom": True,
            "max_scrolls": 10,
            "wait_seconds": 3,
            "is_active": True,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }

        resp = client.post(
            "/api/pages",
            json={
                "url": "https://example.com/path",
                "name": "New Page",
                "project_id": "project-id",
            },
        )

        assert resp.status_code == 201
        created_payload = mock_create.await_args.args[0]
        assert created_payload["project_id"] == "project-id"

    def test_create_page_invalid_viewport(self, client):
        resp = client.post(
            "/api/pages",
            json={"url": "https://example.com", "viewport_width": 50},
        )
        assert resp.status_code == 422
