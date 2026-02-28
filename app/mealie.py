import contextlib
import re
import uuid

import httpx

from app.config import AppConfig

_SLUG_RE = re.compile(r"^[a-zA-Z0-9\-]+$")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _validate_slug(slug: str) -> None:
    """Raise ValueError if slug contains unexpected characters."""
    if not _SLUG_RE.match(slug):
        raise ValueError(f"Unexpected slug format from Mealie: {slug!r}")


async def fetch_user_info(mealie_url: str, token: str) -> dict:
    """Fetch user/household/group UUIDs from Mealie."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{mealie_url}/api/users/self",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "mealie_user_id": data["id"],
            "mealie_household_id": data["householdId"],
            "mealie_group_id": data["groupId"],
        }


async def create_recipe(
    mealie_url: str,
    token: str,
    name: str,
    http_client: httpx.AsyncClient | None = None,
) -> tuple[str, str]:
    """Create a blank recipe, return (slug, recipe_id)."""
    cm = contextlib.nullcontext(http_client) if http_client else httpx.AsyncClient()
    async with cm as client:
        resp = await client.post(
            f"{mealie_url}/api/recipes",
            headers={**_headers(token), "Content-Type": "application/json"},
            json={"name": name},
            timeout=10,
        )
        resp.raise_for_status()
        slug = resp.json()
        _validate_slug(slug)

        resp = await client.get(
            f"{mealie_url}/api/recipes/{slug}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        recipe = resp.json()
        return slug, recipe["id"]


async def update_recipe(
    mealie_url: str,
    token: str,
    slug: str,
    payload: dict,
    http_client: httpx.AsyncClient | None = None,
) -> dict:
    """PUT the full recipe JSON to Mealie."""
    cm = contextlib.nullcontext(http_client) if http_client else httpx.AsyncClient()
    async with cm as client:
        resp = await client.put(
            f"{mealie_url}/api/recipes/{slug}",
            headers={**_headers(token), "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def upload_hero_image(
    mealie_url: str,
    token: str,
    slug: str,
    image_bytes: bytes,
    http_client: httpx.AsyncClient | None = None,
) -> str:
    """Upload hero image to Mealie. Returns the image token to set on the recipe."""
    cm = contextlib.nullcontext(http_client) if http_client else httpx.AsyncClient()
    async with cm as client:
        resp = await client.put(
            f"{mealie_url}/api/recipes/{slug}/image",
            headers=_headers(token),
            files={"image": ("original.webp", image_bytes, "image/webp")},
            data={"extension": "webp"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["image"]


def build_recipe_payload(
    structured: dict,
    recipe_id: str,
    slug: str,
    config: AppConfig,
    image_token: str | None = None,
) -> dict:
    """Convert Claude-structured recipe data into a valid Mealie JSON payload."""
    ingredients = [
        {
            "quantity": None,
            "unit": None,
            "food": None,
            "note": ing["text"],
            "display": ing["text"],
            "title": ing.get("sectionTitle"),
            "originalText": ing["text"],
            "referenceId": str(uuid.uuid4()),
        }
        for ing in structured.get("ingredients", [])
    ]

    instructions = [
        {
            "id": None,
            "title": step.get("sectionTitle") or "",
            "summary": "",
            "text": step["text"],
            "ingredientReferences": [],
        }
        for step in structured.get("instructions", [])
    ]

    notes = []
    if structured.get("notes"):
        notes.append({"title": "Notes", "text": structured["notes"]})

    servings = structured.get("recipeServings") or 0

    return {
        "id": recipe_id,
        "userId": config.mealie_user_id,
        "householdId": config.mealie_household_id,
        "groupId": config.mealie_group_id,
        "name": structured["name"],
        "slug": slug,
        "image": image_token,
        "recipeServings": servings,
        "recipeYieldQuantity": servings,
        "recipeYield": structured.get("recipeYield") or "",
        "totalTime": structured.get("totalTime") or "",
        "prepTime": structured.get("prepTime") or "",
        "cookTime": structured.get("cookTime") or "",
        "performTime": structured.get("cookTime") or "",
        "description": structured.get("description") or "",
        "recipeCategory": [],
        "tags": [],
        "tools": [],
        "rating": None,
        "orgURL": None,
        "recipeIngredient": ingredients,
        "recipeInstructions": instructions,
        "nutrition": {
            "calories": None,
            "carbohydrateContent": None,
            "cholesterolContent": None,
            "fatContent": None,
            "fiberContent": None,
            "proteinContent": None,
            "saturatedFatContent": None,
            "sodiumContent": None,
            "sugarContent": None,
            "transFatContent": None,
            "unsaturatedFatContent": None,
        },
        "settings": {
            "public": False,
            "showNutrition": False,
            "showAssets": False,
            "landscapeView": False,
            "disableComments": False,
            "locked": False,
        },
        "assets": [],
        "notes": notes,
        "extras": {},
        "comments": [],
    }
