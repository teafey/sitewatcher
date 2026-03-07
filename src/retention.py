from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from src import db
from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_SNAPSHOTS = 30


async def cleanup_old_snapshots(max_versions: int = DEFAULT_MAX_SNAPSHOTS) -> dict[str, int]:
    """Remove old snapshots beyond the retention limit.

    Keeps:
    - The latest snapshot (current baseline) regardless of changes
    - Up to max_versions snapshots with has_changes=true
    - Deletes everything else (files + DB records)
    """
    pages = await db.get_all_pages()
    total_deleted = 0
    total_freed_bytes = 0

    for page in pages:
        page_id = page["id"]
        try:
            deleted, freed = await _cleanup_page(page_id, max_versions)
            total_deleted += deleted
            total_freed_bytes += freed
        except Exception as exc:
            logger.error("Retention cleanup failed for page %s: %s", page_id, exc)

    logger.info(
        "Retention cleanup complete: %d snapshots deleted, %.1f MB freed",
        total_deleted,
        total_freed_bytes / (1024 * 1024),
    )
    return {"deleted": total_deleted, "freed_bytes": total_freed_bytes}


async def _cleanup_page(page_id: str, max_versions: int) -> tuple[int, int]:
    # Get all snapshots for this page, newest first
    all_snapshots = await db.get_snapshots(page_id, limit=1000, offset=0)

    if len(all_snapshots) <= 1:
        return 0, 0  # Keep at least the current baseline

    # Always keep the latest snapshot
    latest = all_snapshots[0]
    rest = all_snapshots[1:]

    # Among the rest, keep up to max_versions with changes
    changed = [s for s in rest if s.get("has_changes")]
    unchanged = [s for s in rest if not s.get("has_changes")]

    # Keep the most recent changed snapshots up to limit
    to_keep_changed = changed[:max_versions]
    to_delete = changed[max_versions:] + unchanged

    deleted_count = 0
    freed_bytes = 0

    for snapshot in to_delete:
        freed = _delete_snapshot_files(snapshot)
        freed_bytes += freed
        try:
            await db.delete_snapshot(snapshot["id"])
            deleted_count += 1
        except Exception as exc:
            logger.warning("Failed to delete snapshot %s: %s", snapshot["id"], exc)

    return deleted_count, freed_bytes


def _delete_snapshot_files(snapshot: dict[str, Any]) -> int:
    """Delete files associated with a snapshot. Returns bytes freed."""
    freed = 0

    for path_key in ("screenshot_path", "diff_image_path"):
        path_str = snapshot.get(path_key)
        if path_str:
            path = Path(path_str)
            if path.exists():
                freed += path.stat().st_size
                # Delete the parent directory (timestamp dir) if it only contains this page's files
                parent = path.parent
                if parent.exists():
                    shutil.rmtree(parent, ignore_errors=True)

    return freed
