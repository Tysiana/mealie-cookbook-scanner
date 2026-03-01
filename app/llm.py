from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config import AppConfig


class LLMProvider(ABC):
    @abstractmethod
    def structure_recipe(self, text: str) -> dict: ...

    @abstractmethod
    def structure_recipe_from_image(self, image_bytes: bytes) -> dict: ...


def _parse_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return json.loads(raw)


def get_provider(config: AppConfig) -> LLMProvider:
    if config.llm_provider == "gemini":
        from app.providers.gemini import GeminiProvider
        return GeminiProvider(config.llm_key)
    from app.providers.anthropic import AnthropicProvider
    return AnthropicProvider(config.llm_key)
