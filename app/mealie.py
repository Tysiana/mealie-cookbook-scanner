import uuid
import httpx
from typing import Optional


def get_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def fetch_user_info(mealie_url: str, token: str) -> dict:
    """Fetch user/household/group UUIDs from Mealie."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{mealie_url}/api/users/self",
            headers=get_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "mealie_user_id": data["id"],
            "mealie_household_id": data["householdId"],
            "mealie_group_id": data["groupId"],
        }


async def create_recipe(mealie_url: str, token: str, name: str) -> tuple[str, str]:
    """Create a blank recipe, return (slug, recipe_id)."""
    async with httpx.AsyncClient() as client:
        # Create blank recipe — returns slug string
        resp = await client.post(
            f"{mealie_url}/api/recipes",
            headers={**get_headers(token), "Content-Type": "application/json"},
            json={"name": name},
            timeout=10,
        )
        resp.raise_for_status()
        slug = resp.json()

        # Fetch full recipe to get the ID
        resp = await client.get(
            f"{mealie_url}/api/recipes/{slug}",
            headers=get_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        recipe = resp.json()
        return slug, recipe["id"]


async def update_recipe(mealie_url: str, token: str, slug: str, payload: dict) -> dict:
    """PUT the full recipe JSON to Mealie."""
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{mealie_url}/api/recipes/{slug}",
            headers={**get_headers(token), "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def upload_hero_image(mealie_url: str, token: str, recipe_id: str, image_bytes: bytes) -> None:
    """Upload hero image to Mealie."""
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{mealie_url}/api/media/recipes/{recipe_id}/images/original.webp",
            headers=get_headers(token),
            files={"image": ("original.webp", image_bytes, "image/webp")},
            timeout=30,
        )
        resp.raise_for_status()


def build_recipe_payload(
    structured: dict,
    recipe_id: str,
    slug: str,
    user_id: str,
    household_id: str,
    group_id: str,
) -> dict:
    """Convert Claude-structured recipe data into a valid Mealie JSON payload."""
    ingredients = []
    for i, ing in enumerate(structured.get("ingredients", []), start=1):
        ingredients.append({
            "quantity": None,
            "unit": None,
            "food": None,
            "note": ing["text"],
            "display": ing["text"],
            "title": ing.get("sectionTitle"),
            "originalText": ing["text"],
            "referenceId": str(uuid.uuid4()),
        })

    instructions = []
    for step in structured.get("instructions", []):
        instructions.append({
            "id": None,
            "title": step.get("sectionTitle") or "",
            "summary": "",
            "text": step["text"],
            "ingredientReferences": [],
        })

    notes = []
    if structured.get("notes"):
        notes.append({"title": "Notes", "text": structured["notes"]})

    servings = structured.get("recipeServings") or 0

    return {
        "id": recipe_id,
        "userId": user_id,
        "householdId": household_id,
        "groupId": group_id,
        "name": structured["name"],
        "slug": slug,
        "image": None,
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
            "calories": None, "carbohydrateContent": None, "cholesterolContent": None,
            "fatContent": None, "fiberContent": None, "proteinContent": None,
            "saturatedFatContent": None, "sodiumContent": None, "sugarContent": None,
            "transFatContent": None, "unsaturatedFatContent": None,
        },
        "settings": {
            "public": False, "showNutrition": False, "showAssets": False,
            "landscapeView": False, "disableComments": False, "locked": False,
        },
        "assets": [],
        "notes": notes,
        "extras": {},
        "comments": [],
    }
