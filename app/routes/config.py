import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import config as cfg
from app.mealie import fetch_user_info

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_UPLOAD_MB = 10


class ConfigPayload(BaseModel):
    mealie_url: str
    mealie_token: str
    anthropic_key: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/config")
def get_config():
    config = cfg.load_config()
    if not config:
        return {"configured": False}
    # Never return raw credentials — only signal they are set
    return {
        "configured": True,
        "mealie_url": config.mealie_url,
        "mealie_token_set": True,
        "anthropic_key_set": True,
    }


@router.post("/config")
async def save_config(payload: ConfigPayload):
    mealie_url = payload.mealie_url.rstrip("/")
    try:
        uuids = await fetch_user_info(mealie_url, payload.mealie_token)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not connect to Mealie at {mealie_url}: {e}",
        )

    cfg.save_config(
        {
            "mealie_url": mealie_url,
            "mealie_token": payload.mealie_token,
            "anthropic_key": payload.anthropic_key,
            **uuids,
        }
    )
    return {"ok": True}
