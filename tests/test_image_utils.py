"""Unit tests for app.image_utils — resize and format helpers."""

import io

import pytest
from PIL import Image

from app.image_utils import prepare_hero_image, prepare_vision_image


def _make_image(width: int, height: int, fmt: str = "JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _image_size(image_bytes: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(image_bytes)).size


def test_prepare_vision_image_returns_jpeg():
    jpeg = _make_image(100, 100)
    result = prepare_vision_image(jpeg)
    img = Image.open(io.BytesIO(result))
    assert img.format == "JPEG"


def test_prepare_vision_image_downsizes_large_image():
    # 3000×3000 must shrink to fit within 1568×1568
    big_jpeg = _make_image(3000, 3000)
    result = prepare_vision_image(big_jpeg)
    w, h = _image_size(result)
    assert w <= 1568 and h <= 1568


def test_prepare_vision_image_keeps_small_image_size():
    small = _make_image(100, 80)
    result = prepare_vision_image(small)
    w, h = _image_size(result)
    assert w == 100 and h == 80


def test_prepare_hero_image_returns_webp():
    jpeg = _make_image(200, 200)
    result = prepare_hero_image(jpeg)
    img = Image.open(io.BytesIO(result))
    assert img.format == "WEBP"


def test_prepare_hero_image_downsizes_large_image():
    big = _make_image(2400, 1600)
    result = prepare_hero_image(big)
    w, h = _image_size(result)
    assert w <= 1200 and h <= 800


def test_prepare_hero_image_converts_rgba_to_rgb():
    img = Image.new("RGBA", (100, 100), color=(0, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = prepare_hero_image(buf.getvalue())
    out_img = Image.open(io.BytesIO(result))
    assert out_img.mode == "RGB"
