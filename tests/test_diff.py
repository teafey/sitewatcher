"""Tests for the diff engine."""

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from src.diff import pixel_diff, text_diff, compare


def _create_test_image(width: int, height: int, color: tuple = (255, 255, 255)) -> Path:
    """Create a temporary test image."""
    img = Image.new("RGB", (width, height), color)
    path = Path(tempfile.mktemp(suffix=".png"))
    img.save(str(path))
    return path


def test_identical_images_zero_diff():
    """Comparing identical images should yield 0% difference."""
    img_path = _create_test_image(100, 100, (200, 200, 200))
    result = pixel_diff(img_path, img_path)
    assert result.percent == 0.0
    img_path.unlink()


def test_different_images_nonzero_diff():
    """Comparing different images should yield > 0% difference."""
    img1 = _create_test_image(100, 100, (255, 0, 0))
    img2 = _create_test_image(100, 100, (0, 0, 255))
    result = pixel_diff(img1, img2)
    assert result.percent > 0
    img1.unlink()
    img2.unlink()


def test_diff_image_generated():
    """Diff image should be created when output_path is specified."""
    img1 = _create_test_image(100, 100, (255, 0, 0))
    img2 = _create_test_image(100, 100, (0, 255, 0))
    output = Path(tempfile.mktemp(suffix=".png"))
    result = pixel_diff(img1, img2, output_path=output)
    assert result.diff_image_path is not None
    assert Path(result.diff_image_path).exists()
    img1.unlink()
    img2.unlink()
    output.unlink(missing_ok=True)


def test_tolerance_filters_subtle_changes():
    """Subtle pixel differences within tolerance should not be flagged."""
    img = Image.new("RGB", (100, 100), (128, 128, 128))
    path1 = Path(tempfile.mktemp(suffix=".png"))
    img.save(str(path1))

    # Create slightly different image (within default tolerance of 30)
    arr = np.array(img, dtype=np.uint8)
    arr[:, :] = [130, 130, 130]  # Only 2 units different
    img2 = Image.fromarray(arr)
    path2 = Path(tempfile.mktemp(suffix=".png"))
    img2.save(str(path2))

    result = pixel_diff(path1, path2, tolerance=30)
    assert result.percent == 0.0
    path1.unlink()
    path2.unlink()


def test_different_sizes_handled():
    """Images of different sizes should be resized and compared."""
    img1 = _create_test_image(100, 100, (255, 0, 0))
    img2 = _create_test_image(200, 200, (0, 255, 0))
    result = pixel_diff(img1, img2)
    assert result.percent > 0
    img1.unlink()
    img2.unlink()


def test_text_diff_no_changes():
    """Identical texts should show no changes."""
    result = text_diff("hello world", "hello world")
    assert not result.has_changes
    assert result.unified_diff == ""


def test_text_diff_with_changes():
    """Different texts should show unified diff."""
    result = text_diff("hello", "hello world")
    assert result.has_changes
    assert len(result.unified_diff) > 0


def test_compare_function():
    """Compare should combine pixel and text diffs."""
    img1 = _create_test_image(100, 100, (255, 0, 0))
    img2 = _create_test_image(100, 100, (0, 255, 0))

    with tempfile.TemporaryDirectory() as tmpdir:
        result = compare(
            old_screenshot_path=str(img1),
            old_dom_text="old text",
            new_screenshot_path=str(img2),
            new_dom_text="new text",
            diff_output_dir=tmpdir,
        )
        assert result.has_changes
        assert result.pixel_diff_percent > 0
        assert result.text_has_changes

    img1.unlink()
    img2.unlink()
