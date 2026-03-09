from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from src import db
from src.capture import PageCapture, CaptureResult
from src.config import settings
from src.diff import compare

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


def _run_sync(func, *args, **kwargs):
    """Run sync function in executor without copying contextvars."""
    loop = asyncio.get_running_loop()
    if kwargs:
        import functools
        func = functools.partial(func, *args, **kwargs)
        return loop.run_in_executor(_executor, func)
    return loop.run_in_executor(_executor, func, *args)


async def run_check_cycle() -> dict[str, Any]:
    """Run a full check cycle for all active pages."""
    pages = await db.get_active_pages()
    logger.info("Starting check cycle: %d active pages", len(pages))

    results = {"checked": 0, "changes": 0, "errors": 0}

    capture_engine = await _run_sync(PageCapture.create)
    try:
        for page in pages:
            try:
                result = await _check_page(page, capture_engine)
                results["checked"] += 1
                if result.get("has_changes"):
                    results["changes"] += 1
            except Exception as exc:
                results["errors"] += 1
                logger.error("Failed to check page %s: %s", page.get("name", page["id"]), exc)
    finally:
        await _run_sync(capture_engine.stop)

    logger.info(
        "Check cycle complete: %d checked, %d changes, %d errors",
        results["checked"], results["changes"], results["errors"],
    )
    return results


async def check_single_page(page_id: str) -> dict[str, Any]:
    """Check a single page by ID."""
    page = await db.get_page(page_id)
    if not page:
        raise ValueError(f"Page {page_id} not found")

    capture_engine = await _run_sync(PageCapture.create)
    try:
        return await _check_page(page, capture_engine)
    finally:
        await _run_sync(capture_engine.stop)


async def _check_page(
    page: dict[str, Any],
    capture_engine: PageCapture,
) -> dict[str, Any]:
    page_name = page.get("name") or page["url"]
    page_id = page["id"]
    logger.info("Checking page: %s", page_name)

    # Extract viewports (multi-viewport or fallback to single)
    viewports_raw = page.get("viewports")
    if viewports_raw and isinstance(viewports_raw, list) and len(viewports_raw) > 0:
        viewports = [(v["width"], v["height"]) for v in viewports_raw]
    else:
        viewports = [(page.get("viewport_width", 1920), page.get("viewport_height", 1080))]

    combined_result: dict[str, Any] = {"has_changes": False, "diff_percent": 0.0}

    for vw, vh in viewports:
        result = await _check_page_viewport(page, capture_engine, vw, vh)
        if result.get("error"):
            combined_result.setdefault("errors", []).append(result["error"])
        if result.get("has_changes"):
            combined_result["has_changes"] = True
        if (result.get("diff_percent") or 0) > (combined_result.get("diff_percent") or 0):
            combined_result["diff_percent"] = result["diff_percent"]

    return combined_result


async def _check_page_viewport(
    page: dict[str, Any],
    capture_engine: PageCapture,
    viewport_width: int,
    viewport_height: int,
) -> dict[str, Any]:
    page_name = page.get("name") or page["url"]
    page_id = page["id"]
    viewport_label = f"{viewport_width}x{viewport_height}"
    logger.info("Checking page: %s [%s]", page_name, viewport_label)

    # Capture with retry
    capture_result = await _capture_with_retry(page, capture_engine, viewport=(viewport_width, viewport_height))

    if capture_result.error:
        # Save error snapshot
        await db.create_snapshot({
            "page_id": page_id,
            "error_message": capture_result.error,
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
        })
        logger.warning("Capture failed for %s [%s]: %s", page_name, viewport_label, capture_result.error)
        return {"has_changes": False, "error": capture_result.error}

    # Get previous snapshot for this viewport
    prev_snapshot = await db.get_latest_snapshot(page_id, viewport_width=viewport_width, viewport_height=viewport_height)

    # Compare if we have a previous snapshot
    has_changes = False
    diff_percent: float | None = None
    diff_image_path: str | None = None
    text_diff_str: str = ""

    if prev_snapshot and prev_snapshot.get("screenshot_path"):
        prev_screenshot = prev_snapshot["screenshot_path"]
        prev_dom = prev_snapshot.get("dom_text", "")

        output_dir = Path(capture_result.screenshot_path).parent if capture_result.screenshot_path else settings.data_dir
        diff_result = await _run_sync(
            compare,
            old_screenshot_path=prev_screenshot,
            old_dom_text=prev_dom,
            new_screenshot_path=capture_result.screenshot_path,
            new_dom_text=capture_result.dom_text,
            diff_output_dir=output_dir,
        )

        threshold = page.get("diff_threshold", 0.5)
        has_changes = diff_result.pixel_diff_percent > threshold or diff_result.text_has_changes
        diff_percent = diff_result.pixel_diff_percent
        diff_image_path = diff_result.diff_image_path
        text_diff_str = diff_result.text_diff

    # Save new snapshot
    snapshot_data: dict[str, Any] = {
        "page_id": page_id,
        "screenshot_path": capture_result.screenshot_path,
        "dom_text": capture_result.dom_text,
        "dom_hash": capture_result.dom_hash,
        "diff_percent": diff_percent,
        "diff_image_path": diff_image_path,
        "text_diff": text_diff_str if text_diff_str else None,
        "has_changes": has_changes,
        "viewport_width": viewport_width,
        "viewport_height": viewport_height,
    }
    new_snapshot = await db.create_snapshot(snapshot_data)

    # Notify if changes detected
    if has_changes:
        logger.info("Changes detected for %s [%s] (%.2f%%)", page_name, viewport_label, diff_percent or 0)
        await _notify(page, new_snapshot)
    else:
        logger.info("No changes for %s [%s]", page_name, viewport_label)

    return {"has_changes": has_changes, "diff_percent": diff_percent}


async def _capture_with_retry(
    page: dict[str, Any],
    capture_engine: PageCapture,
    max_retries: int = 3,
    viewport: tuple[int, int] | None = None,
) -> CaptureResult:
    """Capture with exponential backoff retry."""
    result: CaptureResult | None = None
    for attempt in range(max_retries):
        result = await _run_sync(capture_engine.capture, page, viewport=viewport)
        if result.error is None:
            return result
        if attempt < max_retries - 1:
            delay = 2 ** attempt
            logger.warning(
                "Capture attempt %d failed for %s, retrying in %ds...",
                attempt + 1, page["url"], delay,
            )
            await asyncio.sleep(delay)
    return result  # type: ignore[return-value]


async def _notify(page: dict[str, Any], snapshot: dict[str, Any]) -> None:
    from src.notify import get_notifiers
    for notifier in get_notifiers():
        try:
            await notifier.send_change_alert(page, snapshot)
        except Exception as exc:
            logger.error("Notification failed via %s: %s", type(notifier).__name__, exc)


