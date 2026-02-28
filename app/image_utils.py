import io

from PIL import Image

_VISION_MAX_SIZE = (1568, 1568)
_HERO_MAX_SIZE = (1200, 800)


def prepare_vision_image(image_bytes: bytes) -> bytes:
    """Resize and compress image for Claude vision (max 1568x1568, JPEG 90%)."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(_VISION_MAX_SIZE, Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()


def prepare_hero_image(image_bytes: bytes) -> bytes:
    """Resize and compress image for Mealie hero (max 1200x800, WEBP 85%)."""
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(_HERO_MAX_SIZE, Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="WEBP", quality=85)
    return out.getvalue()
