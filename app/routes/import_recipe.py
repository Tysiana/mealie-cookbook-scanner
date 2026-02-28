import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import config as cfg
from app.image_utils import prepare_hero_image
from app.mealie import build_recipe_payload, create_recipe, update_recipe, upload_hero_image

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/import")
async def import_recipe(
    structured_json: str = Form(...),
    hero_image: Optional[UploadFile] = File(None),
):
    config = cfg.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="App not configured")

    try:
        structured = json.loads(structured_json)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid JSON at line {e.lineno}: {e.msg}",
        )

    # Validate hero image size before reading fully
    if hero_image and hero_image.size and hero_image.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Hero image too large (max 10 MB)")

    # Share one HTTP connection for all Mealie calls in this request
    async with httpx.AsyncClient() as http_client:
        # 1. Create blank recipe to obtain slug + id
        try:
            slug, recipe_id = await create_recipe(
                config.mealie_url, config.mealie_token, structured["name"],
                http_client=http_client,
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to create recipe {structured['name']!r}: {e}",
            )

        # 2. Upload hero image first to get the image token for the payload
        image_token = None
        if hero_image:
            try:
                image_bytes = await hero_image.read()
                if len(image_bytes) > _MAX_UPLOAD_BYTES:
                    raise ValueError("Hero image too large (max 10 MB)")
                webp_bytes = prepare_hero_image(image_bytes)
                image_token = await upload_hero_image(
                    config.mealie_url, config.mealie_token, slug, webp_bytes,
                    http_client=http_client,
                )
            except Exception as e:
                # Non-fatal — recipe saves without image, but log it
                logger.warning("Hero image upload failed for slug %r: %s", slug, e)
                image_token = None

        # 3. Build and PUT the full payload (with image token if upload succeeded)
        payload = build_recipe_payload(
            structured=structured,
            recipe_id=recipe_id,
            slug=slug,
            config=config,
            image_token=image_token,
        )
        try:
            await update_recipe(
                config.mealie_url, config.mealie_token, slug, payload,
                http_client=http_client,
            )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to update recipe {slug!r}: {e}",
            )

    warning = "Image upload failed silently" if hero_image and not image_token else None
    return {"slug": slug, "recipe_id": recipe_id, **({} if not warning else {"warning": warning})}
