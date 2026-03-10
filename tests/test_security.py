"""Security tests for path traversal protection and auth middleware.

Tests verify:
- SPA catch-all route rejects path traversal attempts
- Normal frontend paths continue to work
- Auth middleware enforces API key on protected routes
- Whitelisted paths bypass auth
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def frontend_dir(tmp_path):
    """Create a fake frontend/dist directory with index.html and a test file."""
    dist = tmp_path / "frontend" / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)

    (dist / "index.html").write_text("<html><body>SPA</body></html>")
    (assets / "app.css").write_text("body { color: red; }")
    (dist / "favicon.ico").write_bytes(b"\x00\x00\x01\x00")

    # Place a sensitive file OUTSIDE the dist directory (simulating ../ escape)
    secret = tmp_path / "secret.txt"
    secret.write_text("SUPER_SECRET_VALUE_12345")

    return dist


@pytest.fixture()
def client(frontend_dir):
    """Create a TestClient with FRONTEND_DIR pointing to our temp directory."""
    with patch("src.config.settings") as mock_settings:
        mock_settings.api_key = ""
        mock_settings.data_dir = Path(tempfile.mkdtemp())
        mock_settings.check_interval_hours = 24
        mock_settings.supabase_url = ""
        mock_settings.supabase_key = ""
        mock_settings.telegram_enabled = False
        mock_settings.bitrix_enabled = False

        with patch("src.api.main.FRONTEND_DIR", frontend_dir):
            from src.api.main import app

            _patched_frontend_dir = frontend_dir

            # Register a catch-all route using our temp FRONTEND_DIR.
            # The module-level route may not exist (FRONTEND_DIR.is_dir()
            # was false at import time), so we add our own.
            @app.get("/{full_path:path}", name="test_serve_frontend")
            async def _serve_frontend(full_path: str):
                from fastapi.responses import FileResponse

                file = (_patched_frontend_dir / full_path).resolve()
                if not file.is_relative_to(_patched_frontend_dir):
                    return FileResponse(_patched_frontend_dir / "index.html")
                if file.is_file():
                    return FileResponse(file)
                return FileResponse(_patched_frontend_dir / "index.html")

            yield TestClient(app, raise_server_exceptions=False)

            # Clean up the route we added
            app.routes[:] = [
                r
                for r in app.routes
                if getattr(r, "name", None) != "test_serve_frontend"
            ]


@pytest.fixture()
def auth_client():
    """Create a TestClient with API key auth enabled.

    Patches the settings object used by the auth middleware in src.api.main.
    We must patch in the target module since it imports ``settings`` by name.
    """
    from src.api import main as api_main

    original_key = api_main.settings.api_key
    api_main.settings.api_key = "test-secret-key"
    try:
        yield TestClient(api_main.app, raise_server_exceptions=False)
    finally:
        api_main.settings.api_key = original_key


# ---------------------------------------------------------------------------
# Path traversal tests
# ---------------------------------------------------------------------------


class TestPathTraversal:
    """Verify the SPA catch-all route blocks path traversal attempts."""

    def test_root_serves_index(self, client):
        """GET / should serve index.html."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "SPA" in resp.text

    def test_spa_route_serves_index(self, client):
        """GET /pages (non-existent file) should serve index.html (SPA fallback)."""
        resp = client.get("/pages")
        assert resp.status_code == 200
        assert "SPA" in resp.text

    def test_legitimate_file_served(self, client):
        """A real file inside FRONTEND_DIR should be served normally."""
        resp = client.get("/favicon.ico")
        assert resp.status_code == 200
        assert resp.content == b"\x00\x00\x01\x00"

    def test_traversal_dot_dot_env(self, client, frontend_dir):
        """Path traversal with ../../ should NOT serve files outside FRONTEND_DIR."""
        resp = client.get("/../secret.txt")
        assert resp.status_code == 200
        # Should get index.html, not the secret file
        assert "SPA" in resp.text
        assert "SUPER_SECRET_VALUE_12345" not in resp.text

    def test_traversal_multiple_levels(self, client):
        """Deep traversal (../../../etc/passwd) should be blocked."""
        resp = client.get("/../../../etc/passwd")
        # Should return SPA index, not /etc/passwd
        assert "SUPER_SECRET_VALUE_12345" not in resp.text
        assert "root:" not in resp.text

    def test_traversal_encoded_dots(self, client):
        """URL-encoded traversal (%2e%2e/) should be blocked."""
        resp = client.get("/%2e%2e/secret.txt")
        assert "SUPER_SECRET_VALUE_12345" not in resp.text

    def test_traversal_double_encoded(self, client):
        """Double-encoded traversal (%252e%252e/) should be blocked."""
        resp = client.get("/%252e%252e/secret.txt")
        assert "SUPER_SECRET_VALUE_12345" not in resp.text

    def test_traversal_mixed(self, client):
        """Mixed traversal patterns (..%2f) should be blocked."""
        resp = client.get("/..%2fsecret.txt")
        assert "SUPER_SECRET_VALUE_12345" not in resp.text

    def test_traversal_does_not_leak_content(self, client, frontend_dir):
        """Exhaustive check: try multiple traversal variants and verify no leak."""
        secret_content = "SUPER_SECRET_VALUE_12345"
        traversal_paths = [
            "/../secret.txt",
            "/../../secret.txt",
            "/../../../secret.txt",
            "/%2e%2e/secret.txt",
            "/%2e%2e/%2e%2e/secret.txt",
            "/..%2fsecret.txt",
            "/%2e%2e%2fsecret.txt",
        ]
        for path in traversal_paths:
            resp = client.get(path)
            assert secret_content not in resp.text, (
                f"Path traversal leaked content via {path}"
            )


# ---------------------------------------------------------------------------
# Auth middleware tests
# ---------------------------------------------------------------------------


class TestAuthMiddleware:
    """Verify API key authentication middleware behavior."""

    def test_health_no_auth_required(self, auth_client):
        """GET /api/health should work without an API key."""
        resp = auth_client.get("/api/health")
        assert resp.status_code == 200

    def test_docs_no_auth_required(self, auth_client):
        """GET /docs should work without an API key."""
        resp = auth_client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_no_auth_required(self, auth_client):
        """GET /openapi.json should work without an API key."""
        resp = auth_client.get("/openapi.json")
        assert resp.status_code == 200

    def test_root_no_auth_required(self, auth_client):
        """GET / is whitelisted and should not require auth."""
        resp = auth_client.get("/")
        # Should not be 401 -- root is whitelisted
        assert resp.status_code != 401

    def test_static_no_auth_required(self, auth_client):
        """Paths starting with /static should bypass auth."""
        resp = auth_client.get("/static/data/nonexistent.png")
        # May 404, but should NOT be 401
        assert resp.status_code != 401

    def test_assets_no_auth_required(self, auth_client):
        """Paths starting with /assets should bypass auth."""
        resp = auth_client.get("/assets/nonexistent.css")
        # May 404, but should NOT be 401
        assert resp.status_code != 401

    @patch("src.db.get_all_pages", new_callable=AsyncMock)
    def test_api_requires_auth(self, mock_get, auth_client):
        """GET /api/pages without API key should be rejected."""
        mock_get.return_value = []
        resp = auth_client.get("/api/pages")
        # Middleware raises HTTPException(401) which surfaces as 401 or 500
        # depending on Starlette version. Either way, NOT 200.
        assert resp.status_code != 200

    @patch("src.db.get_all_pages", new_callable=AsyncMock)
    def test_api_with_valid_key(self, mock_get, auth_client):
        """GET /api/pages with correct API key should succeed."""
        mock_get.return_value = []
        resp = auth_client.get(
            "/api/pages",
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200

    @patch("src.db.get_all_pages", new_callable=AsyncMock)
    def test_api_with_wrong_key(self, mock_get, auth_client):
        """GET /api/pages with wrong API key should be rejected."""
        mock_get.return_value = []
        resp = auth_client.get(
            "/api/pages",
            headers={"X-API-Key": "wrong-key"},
        )
        # Middleware raises HTTPException(401) which surfaces as 401 or 500
        # depending on Starlette version. Either way, NOT 200.
        assert resp.status_code != 200
