import logging

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.ocr import _ALLOWED_PSM_VALUES, extract_text

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/tiff"}


@router.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    psm: int = Query(default=3, description="Tesseract page segmentation mode (allowed: 3 4 5 6 7 11 12)"),
):
    if file.size and file.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    if psm not in _ALLOWED_PSM_VALUES:
        raise HTTPException(status_code=400, detail=f"PSM {psm} is not supported for recipe OCR")

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")

    try:
        text = extract_text(image_bytes, psm=psm)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"OCR failed on {file.filename!r}: {e}",
        )
    return {"text": text}
