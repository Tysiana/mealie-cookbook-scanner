import base64
import json
from pathlib import Path

import anthropic

_SYSTEM_PROMPT = "You are a recipe extraction assistant. Given OCR-extracted text from a cookbook page, output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_VISION_SYSTEM = "You are a recipe extraction assistant. You will be shown an image of a cookbook page. Output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_PROMPT_PATH = Path(__file__).parent / "prompts" / "recipe_extraction.md"
_USER_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


def _parse_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(raw)


def structure_recipe(ocr_text: str, anthropic_key: str) -> dict:
    """Send OCR text to Claude and return structured recipe data."""
    client = anthropic.Anthropic(api_key=anthropic_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"{_USER_PROMPT}\n\n## OCR text\n\n{ocr_text}",
            }
        ],
    )
    return _parse_response(message.content[0].text)


def structure_recipe_from_image(image_bytes: bytes, anthropic_key: str) -> dict:
    """Send image directly to Claude vision and return structured recipe data."""
    client = anthropic.Anthropic(api_key=anthropic_key)
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=_VISION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": _USER_PROMPT,
                    },
                ],
            }
        ],
    )
    return _parse_response(message.content[0].text)
