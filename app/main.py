import io
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from PIL import Image

from app import config as cfg
from app.ocr import extract_text
from app.claude import structure_recipe
from app.mealie import (
    fetch_user_info,
    create_recipe,
    update_recipe,
    upload_hero_image,
    build_recipe_payload,
)

app = FastAPI()


# --- Config ---

class ConfigPayload(BaseModel):
    mealie_url: str
    mealie_token: str
    anthropic_key: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    config = cfg.load_config()
    if not config or not cfg.is_configured():
        return {"configured": False}
    return {"configured": True, "mealie_url": config["mealie_url"]}


@app.post("/api/config")
async def save_config(payload: ConfigPayload):
    mealie_url = payload.mealie_url.rstrip("/")
    try:
        uuids = await fetch_user_info(mealie_url, payload.mealie_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not connect to Mealie: {e}")

    cfg.save_config({
        "mealie_url": mealie_url,
        "mealie_token": payload.mealie_token,
        "anthropic_key": payload.anthropic_key,
        **uuids,
    })
    return {"ok": True}


# --- OCR ---

@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)):
    image_bytes = await file.read()
    try:
        text = extract_text(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"OCR failed: {e}")
    return {"text": text}


# --- Structure via Claude ---

class StructurePayload(BaseModel):
    text: str


@app.post("/api/structure")
async def structure(payload: StructurePayload):
    config = cfg.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="App not configured")
    try:
        structured = structure_recipe(payload.text, config["anthropic_key"])
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Claude extraction failed: {e}")
    return structured


# --- Import to Mealie ---

@app.post("/api/import")
async def import_recipe(
    structured_json: str = Form(...),
    hero_image: Optional[UploadFile] = File(None),
):
    import json as _json

    config = cfg.load_config()
    if not config:
        raise HTTPException(status_code=400, detail="App not configured")

    try:
        structured = _json.loads(structured_json)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid structured JSON")

    mealie_url = config["mealie_url"]
    token = config["mealie_token"]

    # 1. Create blank recipe in Mealie
    try:
        slug, recipe_id = await create_recipe(mealie_url, token, structured["name"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create recipe: {e}")

    # 2. Build and PUT the full payload
    payload = build_recipe_payload(
        structured=structured,
        recipe_id=recipe_id,
        slug=slug,
        user_id=config["mealie_user_id"],
        household_id=config["mealie_household_id"],
        group_id=config["mealie_group_id"],
    )
    try:
        await update_recipe(mealie_url, token, slug, payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to update recipe: {e}")

    # 3. Upload hero image if provided
    if hero_image:
        try:
            image_bytes = await hero_image.read()
            webp_bytes = _prepare_hero_image(image_bytes)
            await upload_hero_image(mealie_url, token, recipe_id, webp_bytes)
        except Exception as e:
            # Non-fatal — recipe was saved, just no image
            return {"slug": slug, "recipe_id": recipe_id, "warning": f"Image upload failed: {e}"}

    return {"slug": slug, "recipe_id": recipe_id}


def _prepare_hero_image(image_bytes: bytes, max_size: tuple = (1200, 800)) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail(max_size, Image.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="WEBP", quality=85)
    return out.getvalue()


# --- Frontend ---

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
