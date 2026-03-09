"""Tests for the capture engine.

These tests require Playwright and a browser to be installed.
Run with: pytest tests/test_capture.py -v
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.capture import PageCapture, CaptureResult, _scroll_page


@pytest.fixture
def data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.capture.settings") as mock_settings:
            mock_settings.data_dir = Path(tmpdir)
            yield Path(tmpdir)


def _playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


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


class TestScrollPage:
    def test_scroll_stops_when_height_unchanged(self):
        """Scroll should stop when page height stops changing."""
        mock_page = MagicMock()
        mock_page.evaluate.side_effect = [
            None, 2000,   # scroll 1: height grows
            None, 2000,   # scroll 2: height same → stop
            None,         # scrollTo(0, 0)
        ]
        _scroll_page(mock_page, viewport_height=1080, max_scrolls=10)
        assert mock_page.evaluate.call_count == 5  # 4 in loop + 1 scrollTo
        assert mock_page.wait_for_timeout.call_count == 2

    def test_scroll_respects_max_scrolls(self):
        """Should stop after max_scrolls even if page keeps growing."""
        mock_page = MagicMock()
        heights = []
        for i in range(4):
            heights.append(None)
            heights.append((i + 1) * 1080)
        mock_page.evaluate.side_effect = heights
        _scroll_page(mock_page, viewport_height=1080, max_scrolls=3)
        # 3 scrolls * 2 evaluate calls each + 1 scrollTo = 7
        assert mock_page.evaluate.call_count == 7

    def test_scroll_back_to_top(self):
        """After scrolling, should scroll back to top."""
        mock_page = MagicMock()
        mock_page.evaluate.side_effect = [None, 2000, None, 2000, None]
        _scroll_page(mock_page, viewport_height=1080, max_scrolls=10)
        last_call = mock_page.evaluate.call_args_list[-1]
        assert "scrollTo(0, 0)" in str(last_call)
