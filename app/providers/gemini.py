from pathlib import Path

from google import genai
from google.genai import types

from app.llm import LLMProvider, _parse_response

_SYSTEM_PROMPT = "You are a recipe extraction assistant. Given OCR-extracted text from a cookbook page, output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_VISION_SYSTEM = "You are a recipe extraction assistant. You will be shown an image of a cookbook page. Output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only."

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "recipe_extraction.md"
_USER_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

_MODEL = "gemini-2.0-flash"


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self.__client = genai.Client(api_key=api_key)

    def structure_recipe(self, text: str) -> dict:
        """Send OCR text to Gemini and return structured recipe data."""
        response = self.__client.models.generate_content(
            model=_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
            ),
            contents=f"{_USER_PROMPT}\n\n## OCR text\n\n{text}",
        )
        return _parse_response(response.text)

    def structure_recipe_from_image(self, image_bytes: bytes) -> dict:
        """Send image to Gemini vision and return structured recipe data."""
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        response = self.__client.models.generate_content(
            model=_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=_VISION_SYSTEM,
            ),
            contents=[image_part, _USER_PROMPT],
        )
        return _parse_response(response.text)
