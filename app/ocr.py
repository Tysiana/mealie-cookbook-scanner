import io
import pytesseract
from PIL import Image


def extract_text(image_bytes: bytes) -> str:
    """Run Tesseract OCR on image bytes and return extracted text."""
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if needed (handles RGBA, palette mode, etc.)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    text = pytesseract.image_to_string(image, lang="eng")
    return text.strip()
