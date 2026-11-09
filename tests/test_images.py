"""Tests for photo preparation in app/images.py."""

import base64
import io

import pytest
from PIL import Image

from app.images import MAX_SIDE, PhotoProblem, prepare_image


def photo_bytes(width: int, height: int, orientation: int | None = None) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    buffer = io.BytesIO()
    if orientation:
        exif = Image.Exif()
        exif[0x0112] = orientation  # the "this photo is rotated" tag
        image.save(buffer, format="JPEG", exif=exif)
    else:
        image.save(buffer, format="JPEG")
    return buffer.getvalue()


def decode(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64)))


def test_big_photo_is_shrunk():
    result = decode(prepare_image(photo_bytes(4000, 3000)))
    assert max(result.size) == MAX_SIDE
    assert result.size == (2000, 1500)  # proportions kept


def test_sideways_phone_photo_is_turned_upright():
    # Orientation 6 means "rotate 90° to display". A 1200x800 photo should become 800x1200.
    result = decode(prepare_image(photo_bytes(1200, 800, orientation=6)))
    assert result.size == (800, 1200)


def test_tiny_photo_is_refused():
    with pytest.raises(PhotoProblem) as problem:
        prepare_image(photo_bytes(100, 100))
    assert "closer" in problem.value.tip


def test_non_photo_is_refused():
    with pytest.raises(PhotoProblem):
        prepare_image(b"this is not an image")
