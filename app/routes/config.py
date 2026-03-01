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
    llm_provider: str
    llm_key: str


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
        "llm_key_set": True,
        "llm_provider": config.llm_provider,
    }


@router.get("/models")
def list_gemini_models():
    """Return Gemini models that support generateContent — for debugging key/quota issues."""
    config = cfg.load_config()
    if not config or config.llm_provider != "gemini":
        raise HTTPException(status_code=400, detail="Gemini not configured")
    try:
        from google import genai
        client = genai.Client(api_key=config.llm_key)
        models = [
            m.name for m in client.models.list()
            if hasattr(m, "supported_actions")
            and m.supported_actions
            and "generateContent" in m.supported_actions
        ]
        return {"models": sorted(models)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            "llm_provider": payload.llm_provider,
            "llm_key": payload.llm_key,
            **uuids,
        }
    )
    return {"ok": True}
