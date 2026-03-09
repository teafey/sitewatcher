from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class PixelDiffResult:
    percent: float
    diff_image_path: str | None = None


@dataclass
class TextDiffResult:
    has_changes: bool
    unified_diff: str = ""


@dataclass
class CompareResult:
    pixel_diff_percent: float = 0.0
    text_has_changes: bool = False
    diff_image_path: str | None = None
    text_diff: str = ""
    has_changes: bool = False


def pixel_diff(
    img1_path: str | Path,
    img2_path: str | Path,
    tolerance: int = 30,
    output_path: str | Path | None = None,
) -> PixelDiffResult:
    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")

    # Handle different sizes — resize smaller to match larger
    if img1.size != img2.size:
        logger.warning(
            "Image sizes differ: %s vs %s. Resizing to match.",
            img1.size, img2.size,
        )
        target_w = max(img1.width, img2.width)
        target_h = max(img1.height, img2.height)
        img1 = img1.resize((target_w, target_h), Image.LANCZOS)
        img2 = img2.resize((target_w, target_h), Image.LANCZOS)

    arr1 = np.array(img1, dtype=np.int16)
    arr2 = np.array(img2, dtype=np.int16)

    # Compute absolute difference per channel
    diff = np.abs(arr1 - arr2)

    # Apply tolerance: pixel is "changed" if any channel differs by more than tolerance
    changed_mask = np.any(diff > tolerance, axis=2)
    changed_count = int(np.sum(changed_mask))
    total_pixels = changed_mask.size
    percent = (changed_count / total_pixels) * 100.0

    diff_image_path_str: str | None = None

    if output_path and changed_count > 0:
        # Generate diff image: base image with red overlay on changed areas
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        overlay = np.array(img2, dtype=np.uint8).copy()
        # Set changed pixels to semi-transparent red
        overlay[changed_mask] = [255, 0, 0]

        # Blend: 70% original + 30% overlay
        blended = (np.array(img2, dtype=np.float32) * 0.7 +
                   overlay.astype(np.float32) * 0.3).astype(np.uint8)

        Image.fromarray(blended).save(str(output_path))
        diff_image_path_str = str(output_path)
        logger.info("Diff image saved: %s (%.2f%% changed)", output_path, percent)

    return PixelDiffResult(percent=round(percent, 4), diff_image_path=diff_image_path_str)


def text_diff(text1: str, text2: str) -> TextDiffResult:
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    diff_lines = list(difflib.unified_diff(
        lines1, lines2,
        fromfile="previous",
        tofile="current",
        lineterm="",
    ))

    has_changes = len(diff_lines) > 0
    unified = "\n".join(diff_lines)

    return TextDiffResult(has_changes=has_changes, unified_diff=unified)


def compare(
    old_screenshot_path: str | None,
    old_dom_text: str | None,
    new_screenshot_path: str | None,
    new_dom_text: str,
    diff_output_dir: str | Path,
) -> CompareResult:
    result = CompareResult()
    diff_output_dir = Path(diff_output_dir)

    # Pixel diff
    if old_screenshot_path and new_screenshot_path:
        diff_img_path = diff_output_dir / "diff.png"
        px_result = pixel_diff(
            old_screenshot_path,
            new_screenshot_path,
            output_path=diff_img_path,
        )
        result.pixel_diff_percent = px_result.percent
        result.diff_image_path = px_result.diff_image_path

    # Text diff
    if old_dom_text is not None:
        txt_result = text_diff(old_dom_text, new_dom_text)
        result.text_has_changes = txt_result.has_changes
        result.text_diff = txt_result.unified_diff

    result.has_changes = result.pixel_diff_percent > 0 or result.text_has_changes

    return result
