"""Tests for the capture engine.

These tests require Playwright and a browser to be installed.
Run with: pytest tests/test_capture.py -v
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.capture import PageCapture, CaptureResult


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.capture.settings") as mock_settings:
            mock_settings.data_dir = Path(tmpdir)
            yield Path(tmpdir)


class TestCaptureResult:
    def test_default_captured_at(self):
        result = CaptureResult()
        assert result.captured_at != ""
        assert len(result.captured_at) > 0

    def test_error_result(self):
        result = CaptureResult(error="Connection timeout")
        assert result.error == "Connection timeout"
        assert result.screenshot_path is None


class TestPageCapture:
    @pytest.mark.skipif(
        not _playwright_available(),
        reason="Playwright not installed",
    )
    def test_capture_example_com(self, data_dir):
        config = {
            "id": "test-page-id",
            "url": "https://example.com",
            "viewport_width": 1280,
            "viewport_height": 720,
        }
        with PageCapture() as pc:
            result = pc.capture(config)

        assert result.error is None
        assert result.screenshot_path is not None
        assert Path(result.screenshot_path).exists()
        assert Path(result.screenshot_path).stat().st_size > 10000  # > 10KB
        assert len(result.dom_text) > 0
        assert len(result.dom_hash) == 64  # SHA-256 hex

    @pytest.mark.skipif(
        not _playwright_available(),
        reason="Playwright not installed",
    )
    def test_capture_nonexistent_url(self, data_dir):
        config = {
            "id": "test-error-page",
            "url": "https://nonexistent.example.invalid",
            "viewport_width": 1280,
            "viewport_height": 720,
        }
        with PageCapture() as pc:
            result = pc.capture(config)

        assert result.error is not None


def _playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False
