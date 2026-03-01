import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import config as cfg
from app.image_utils import prepare_vision_image
from app.llm import get_provider

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/tiff"}


class StructurePayload(BaseModel):
    text: str


@router.post("/structure")
async def structure(payload: StructurePayload):
    config = cfg.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="App not configured")
    try:
        structured = get_provider(config).structure_recipe(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"LLM provider extraction failed on {len(payload.text)} chars of text: {e}",
        )
    return structured


@router.post("/structure-image")
async def structure_image(file: UploadFile = File(...)):
    config = cfg.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="App not configured")

    if file.size and file.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")
    if file.content_type and file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        image_bytes = await file.read()
        if len(image_bytes) > _MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")
        compressed = prepare_vision_image(image_bytes)
        structured = get_provider(config).structure_recipe_from_image(compressed)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"LLM provider vision failed on {file.filename!r}: {e}",
        )
    return structured
