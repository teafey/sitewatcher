from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright, Browser, Page

from src.config import settings

logger = logging.getLogger(__name__)


def _scroll_page(page: Page, viewport_height: int, max_scrolls: int) -> None:
    """Scroll down the page to trigger lazy-loaded content."""
    prev_height = 0
    for i in range(max_scrolls):
        page.evaluate(f"window.scrollBy(0, {viewport_height})")
        page.wait_for_timeout(500)
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == prev_height:
            break
        prev_height = current_height
    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")


@dataclass
class CaptureResult:
    screenshot_path: str | None = None
    dom_text: str = ""
    dom_hash: str = ""
    error: str | None = None
    captured_at: str = ""

    def __post_init__(self) -> None:
        if not self.captured_at:
            self.captured_at = datetime.now(timezone.utc).isoformat()


class PageCapture:
    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None

    @classmethod
    def create(cls) -> PageCapture:
        pc = cls()
        pc.start()
        return pc

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        logger.info("Browser launched")

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Browser closed")

    def __enter__(self) -> PageCapture:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()

    def capture(self, page_config: dict[str, Any]) -> CaptureResult:
        page_id = page_config["id"]
        url = page_config["url"]
        viewport_width = page_config.get("viewport_width", 1920)
        viewport_height = page_config.get("viewport_height", 1080)
        wait_for = page_config.get("wait_for_selector")
        ignore_selectors: list[str] = page_config.get("ignore_selectors") or []
        scroll_to_bottom = page_config.get("scroll_to_bottom", True)
        max_scrolls = page_config.get("max_scrolls", 10)
        wait_seconds = page_config.get("wait_seconds", 3)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_dir = settings.data_dir / str(page_id) / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if not self._browser:
                raise RuntimeError("Browser not started. Use 'with PageCapture() as pc:'")

            context = self._browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
            )
            page: Page = context.new_page()

            logger.info("Navigating to %s (viewport: %dx%d)", url, viewport_width, viewport_height)
            page.goto(url, wait_until="networkidle", timeout=60000)

            # Scroll to trigger lazy-loaded content
            if scroll_to_bottom:
                logger.info("Scrolling page (max %d scrolls)", max_scrolls)
                _scroll_page(page, viewport_height, max_scrolls)

            # Wait for visual content to settle
            page.wait_for_timeout(wait_seconds * 1000)

            if wait_for:
                logger.info("Waiting for selector: %s", wait_for)
                page.wait_for_selector(wait_for, timeout=10000)

            # Remove ignored elements
            for selector in ignore_selectors:
                page.evaluate(
                    """(sel) => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    }""",
                    selector,
                )

            # Take screenshot
            screenshot_path = output_dir / "screenshot.png"
            page.screenshot(full_page=True, path=str(screenshot_path))
            logger.info("Screenshot saved: %s", screenshot_path)

            # Extract DOM text
            dom_text = page.inner_text("body")
            dom_hash = hashlib.sha256(dom_text.encode("utf-8")).hexdigest()

            # Save DOM text
            dom_path = output_dir / "dom.txt"
            dom_path.write_text(dom_text, encoding="utf-8")

            context.close()

            return CaptureResult(
                screenshot_path=str(screenshot_path),
                dom_text=dom_text,
                dom_hash=dom_hash,
            )

        except Exception as exc:
            logger.error("Capture failed for %s: %s", url, exc)
            return CaptureResult(error=str(exc))
