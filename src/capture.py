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


def _wait_for_dom_stable(page: Page, stable_ms: int = 1500, timeout_ms: int = 10000) -> None:
    """Wait until DOM stops changing (no mutations for stable_ms)."""
    try:
        page.evaluate(
            """([stableMs, timeoutMs]) => new Promise(resolve => {
                let timer = setTimeout(resolve, stableMs);
                const observer = new MutationObserver(() => {
                    clearTimeout(timer);
                    timer = setTimeout(() => { observer.disconnect(); resolve(); }, stableMs);
                });
                observer.observe(document.body, { childList: true, subtree: true, attributes: true });
                setTimeout(() => { observer.disconnect(); resolve(); }, timeoutMs);
            })""",
            [stable_ms, timeout_ms],
        )
    except Exception:
        pass  # Proceed even if stability check fails


def _scroll_page(page: Page, viewport_height: int, max_scrolls: int) -> None:
    """Scroll down the page to trigger lazy-loaded content."""
    # Remove loading="lazy" so images start loading when scrolled near
    page.evaluate("""() => {
        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
            img.removeAttribute('loading');
        });
    }""")

    prev_height = 0
    for _ in range(max_scrolls):
        page.evaluate(f"window.scrollBy(0, {viewport_height})")
        page.wait_for_timeout(800)
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == prev_height:
            break
        prev_height = current_height

    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")

    # Wait for all images to finish loading
    _wait_for_images(page)


def _wait_for_images(page: Page, timeout_ms: int = 10000) -> None:
    """Wait until all <img> elements are fully loaded."""
    try:
        page.evaluate(
            """(timeoutMs) => new Promise(resolve => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const pending = imgs.filter(img => !img.complete && img.src);
                if (pending.length === 0) return resolve();

                let resolved = false;
                const done = () => { if (!resolved) { resolved = true; resolve(); } };
                setTimeout(done, timeoutMs);

                let count = 0;
                for (const img of pending) {
                    img.addEventListener('load', () => { if (++count >= pending.length) done(); });
                    img.addEventListener('error', () => { if (++count >= pending.length) done(); });
                }
            })""",
            timeout_ms,
        )
    except Exception:
        pass


@dataclass
class CaptureResult:
    screenshot_path: str | None = None
    dom_text: str = ""
    dom_hash: str = ""
    error: str | None = None
    captured_at: str = ""
    viewport_width: int = 0
    viewport_height: int = 0

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

    def capture(
        self,
        page_config: dict[str, Any],
        viewport: tuple[int, int] | None = None,
    ) -> CaptureResult:
        page_id = page_config["id"]
        url = page_config["url"]
        if viewport:
            viewport_width, viewport_height = viewport
        else:
            viewport_width = page_config.get("viewport_width", 1920)
            viewport_height = page_config.get("viewport_height", 1080)
        wait_for = page_config.get("wait_for_selector")
        ignore_selectors: list[str] = page_config.get("ignore_selectors") or []
        scroll_to_bottom = page_config.get("scroll_to_bottom", True)
        max_scrolls = page_config.get("max_scrolls", 10)
        wait_seconds = page_config.get("wait_seconds", 3)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        viewport_label = f"{viewport_width}x{viewport_height}"
        output_dir = settings.data_dir / str(page_id) / viewport_label / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            if not self._browser:
                raise RuntimeError("Browser not started. Use 'with PageCapture() as pc:'")

            context = self._browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
            )
            page: Page = context.new_page()

            logger.info("Navigating to %s (viewport: %dx%d)", url, viewport_width, viewport_height)
            page.goto(url, wait_until="load", timeout=60000)

            # Try to wait for network idle, but don't fail if it doesn't happen
            # (many modern sites never reach networkidle due to analytics, ads, websockets)
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                logger.info("Network did not reach idle for %s, proceeding anyway", url)

            # Wait for DOM to stabilize (JS frameworks finish rendering)
            _wait_for_dom_stable(page)

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
                viewport_width=viewport_width,
                viewport_height=viewport_height,
            )

        except Exception as exc:
            logger.error("Capture failed for %s: %s", url, exc)
            return CaptureResult(error=str(exc), viewport_width=viewport_width, viewport_height=viewport_height)
