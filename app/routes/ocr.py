import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.ocr import extract_text

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/tiff"}


@router.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    if file.size and file.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")

    try:
        text = extract_text(image_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"OCR failed on {file.filename!r}: {e}",
        )
    return {"text": text}
