"""Prepares a photo before it's sent to the AI model.

Phone photos are often huge, sideways or in HEIC format. This file fixes all three,
and refuses files that clearly can't work, with a tip the user can act on.
"""

import base64
import io

from PIL import Image, ImageOps, UnidentifiedImageError

try:  # Lets Pillow open iPhone HEIC photos.
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass

MAX_SIDE = 2000  # pixels. Bigger photos cost more and don't read better.
MIN_SIDE = 300  # pixels. Smaller than this, text can't be read.


class PhotoProblem(Exception):
    """The photo can't be used. `tip` tells the user what to do instead."""

    def __init__(self, message: str, tip: str):
        super().__init__(message)
        self.message = message
        self.tip = tip


def prepare_image(image_bytes: bytes) -> str:
    """Return the photo as a base64-encoded JPEG, upright and at most MAX_SIDE pixels."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise PhotoProblem(
            "This file isn't a photo the app can open.",
            "Upload a JPG, PNG or HEIC photo of the document.",
        )

    # Phones store "this photo is sideways" as a tag instead of rotating the pixels.
    image = ImageOps.exif_transpose(image)

    if min(image.size) < MIN_SIDE:
        raise PhotoProblem(
            "The photo is too small to read.",
            "Take the photo closer, so the page fills the screen.",
        )

    image = image.convert("RGB")  # JPEG has no transparency
    image.thumbnail((MAX_SIDE, MAX_SIDE))  # shrinks only if bigger, keeps proportions

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
