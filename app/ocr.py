import io

import pytesseract
from PIL import Image, ImageOps

_MIN_OCR_WIDTH = 1500
_ALLOWED_PSM_VALUES = frozenset({3, 4, 5, 6, 7, 11, 12})


def _preprocess(image: Image.Image) -> Image.Image:
    """Prepare a PIL image for Tesseract OCR.

    Applies grayscale conversion, minimum-width upscaling, and contrast
    normalisation. UnsharpMask is intentionally omitted — it amplifies
    food-photo texture (common on recipe cards) into patterns that
    Tesseract misreads as characters.

    Args:
        image: Any-mode PIL image.

    Returns:
        Grayscale PIL image ready for pytesseract.
    """
    image = image.convert("L")

    if image.width < _MIN_OCR_WIDTH:
        scale = _MIN_OCR_WIDTH / image.width
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # cutoff=2 clips the top/bottom 2% of pixels before stretching the
    # histogram — prevents photo highlights and shadows from anchoring
    # the rescaling and washing out the actual text contrast.
    image = ImageOps.autocontrast(image, cutoff=2)

    return image


def extract_text(image_bytes: bytes, psm: int = 3) -> str:
    """Run Tesseract OCR on image bytes and return extracted text.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG, WebP, etc.).
        psm: Tesseract page segmentation mode.
            3 = fully automatic (default, suitable for full-page scans).
            6 = single uniform block (suitable for user-drawn zone crops).

    Returns:
        Stripped OCR text string.
    """
    if psm not in _ALLOWED_PSM_VALUES:
        raise ValueError(f"Unsupported PSM value: {psm}. Allowed: {sorted(_ALLOWED_PSM_VALUES)}")
    image = Image.open(io.BytesIO(image_bytes))
    image = _preprocess(image)
    config = f"--oem 1 --dpi 300 --psm {psm}"
    text = pytesseract.image_to_string(image, lang="eng", config=config)
    return text.strip()
