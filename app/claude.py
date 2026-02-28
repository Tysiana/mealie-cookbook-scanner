import json
import anthropic

SYSTEM_PROMPT = """You are a recipe extraction assistant. Given OCR-extracted text from a cookbook page, output ONLY a valid JSON object with these exact fields. No explanation, no markdown, no backticks — raw JSON only.

Required fields:
- name (string)
- description (string, the intro/headnote if present, else "")
- totalTime (string, e.g. "1 hour", or "" if unknown)
- prepTime (string, e.g. "30 mins", or "" if unknown)
- cookTime (string, e.g. "30 mins", or "" if unknown)
- recipeYield (string, e.g. "6-8 servings", or "" if unknown)
- recipeServings (integer, best estimate, or 0 if unknown)
- ingredients (array of objects):
  - text: full ingredient string including quantity and unit
  - sectionTitle: section header like "For the Stew" if this ingredient starts a new section, else null
- instructions (array of objects):
  - text: full instruction paragraph
  - sectionTitle: section header like "Prepare the Stew" if present, else null
- notes (string or null, any tip/note sections at the end)

If a field cannot be determined, use null or "" as appropriate."""


def structure_recipe(ocr_text: str, anthropic_key: str) -> dict:
    """Send OCR text to Claude and return structured recipe data."""
    client = anthropic.Anthropic(api_key=anthropic_key)

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extract the recipe from this OCR text:\n\n{ocr_text}",
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if the model added them despite instructions
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(raw)
