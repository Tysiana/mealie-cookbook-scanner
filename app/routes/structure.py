import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import config as cfg
from app.claude import structure_recipe, structure_recipe_from_image
from app.image_utils import prepare_vision_image

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
        structured = structure_recipe(payload.text, config.anthropic_key)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Claude extraction failed on {len(payload.text)} chars of text: {e}",
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
        structured = structure_recipe_from_image(compressed, config.anthropic_key)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Claude vision failed on {file.filename!r}: {e}",
        )
    return structured
