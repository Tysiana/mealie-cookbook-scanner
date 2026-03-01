import base64
from pathlib import Path

import anthropic

from app.llm import LLMProvider, _parse_response

_SYSTEM_PROMPT = "You are a recipe extraction assistant. Given OCR-extracted text from a cookbook page, output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_VISION_SYSTEM = "You are a recipe extraction assistant. You will be shown an image of a cookbook page. Output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "recipe_extraction.md"
_USER_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self.__api_key = api_key

    def structure_recipe(self, text: str) -> dict:
        """Send OCR text to Claude and return structured recipe data."""
        client = anthropic.Anthropic(api_key=self.__api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"{_USER_PROMPT}\n\n## OCR text\n\n{text}",
                }
            ],
        )
        return _parse_response(message.content[0].text)

    def structure_recipe_from_image(self, image_bytes: bytes) -> dict:
        """Send image directly to Claude vision and return structured recipe data."""
        client = anthropic.Anthropic(api_key=self.__api_key)
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
