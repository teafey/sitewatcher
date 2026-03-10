"""Tests for the FastAPI projects API."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
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


class TestProjectsAPI:
    @patch("src.db.get_project_rows", new_callable=AsyncMock)
    def test_list_projects(self, mock_get_rows, client):
        mock_get_rows.return_value = [
            {
                "id": "project-id",
                "name": "example.com",
                "base_url": "https://example.com",
                "pages_count": 2,
                "attention_count": 1,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]

        resp = client.get("/api/projects")

        assert resp.status_code == 200
        assert resp.json()[0]["attention_count"] == 1

    @patch("src.db.create_project", new_callable=AsyncMock)
    @patch("src.db.get_project_by_hostname", new_callable=AsyncMock)
    @patch("src.db.prepare_project_payload", new_callable=AsyncMock)
    def test_create_project(
        self,
        mock_prepare,
        mock_get_by_hostname,
        mock_create,
        client,
    ):
        mock_prepare.return_value = {
            "name": "Example",
            "base_url": "https://example.com",
            "hostname": "example.com",
        }
        mock_get_by_hostname.return_value = None
        mock_create.return_value = {
            "id": "project-id",
            "name": "Example",
            "base_url": "https://example.com",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }

        resp = client.post(
            "/api/projects",
            json={"name": "Example", "base_url": "https://example.com"},
        )

        assert resp.status_code == 201
        assert resp.json()["base_url"] == "https://example.com"

    @patch("src.db.get_project", new_callable=AsyncMock)
    @patch("src.db.get_project_pages", new_callable=AsyncMock)
    def test_get_project_pages(self, mock_get_pages, mock_get_project, client):
        mock_get_project.return_value = {
            "id": "project-id",
            "name": "Example",
            "base_url": "https://example.com",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        mock_get_pages.return_value = [
            {
                "id": "page-id",
                "url": "https://example.com/page",
                "name": "Page",
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

        resp = client.get("/api/projects/project-id/pages")

        assert resp.status_code == 200
        assert resp.json()[0]["project_id"] == "project-id"
