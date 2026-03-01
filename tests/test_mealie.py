"""Unit tests for app.mealie — slug validation and payload builder."""

import uuid

import pytest

from app.config import AppConfig
from app.mealie import _validate_slug, build_recipe_payload


_SAMPLE_CONFIG = AppConfig(
    mealie_url="http://mealie.test",
    mealie_token="tok",
    llm_provider="anthropic",
    llm_key="key",
    mealie_user_id="user-1",
    mealie_household_id="hh-1",
    mealie_group_id="grp-1",
)

_SAMPLE_STRUCTURED = {
    "name": "Banana Bread",
    "description": "A moist loaf.",
    "recipeServings": 8,
    "recipeYield": "1 loaf",
    "prepTime": "15 minutes",
    "cookTime": "60 minutes",
    "totalTime": "75 minutes",
    "ingredients": [
        {"text": "3 ripe bananas"},
        {"text": "200 g flour", "sectionTitle": "Dry"},
    ],
    "instructions": [
        {"text": "Mash bananas."},
        {"text": "Mix in flour.", "sectionTitle": "Batter"},
    ],
    "notes": "Keeps for 3 days.",
}


# ---------------------------------------------------------------------------
# _validate_slug
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", ["banana-bread", "recipe-123", "ABC"])
def test_validate_slug_accepts_valid(slug):
    _validate_slug(slug)  # should not raise


@pytest.mark.parametrize("slug", ["../evil", "recipe/path", "with space", ""])
def test_validate_slug_rejects_invalid(slug):
    with pytest.raises(ValueError):
        _validate_slug(slug)


# ---------------------------------------------------------------------------
# build_recipe_payload
# ---------------------------------------------------------------------------


def test_payload_basic_fields():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    assert payload["name"] == "Banana Bread"
    assert payload["slug"] == "banana-bread"
    assert payload["id"] == "id-abc"
    assert payload["userId"] == "user-1"
    assert payload["householdId"] == "hh-1"
    assert payload["groupId"] == "grp-1"


def test_payload_ingredients_mapped():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    ings = payload["recipeIngredient"]
    assert len(ings) == 2
    assert ings[0]["note"] == "3 ripe bananas"
    assert ings[1]["title"] == "Dry"


def test_payload_instructions_mapped():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    steps = payload["recipeInstructions"]
    assert len(steps) == 2
    assert steps[0]["text"] == "Mash bananas."
    assert steps[1]["title"] == "Batter"


def test_payload_notes_mapped():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    assert payload["notes"] == [{"title": "Notes", "text": "Keeps for 3 days."}]


def test_payload_image_token_included():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
        image_token="img-token-xyz",
    )
    assert payload["image"] == "img-token-xyz"


def test_payload_image_token_none_when_omitted():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    assert payload["image"] is None


def test_payload_reference_ids_are_valid_uuids():
    payload = build_recipe_payload(
        structured=_SAMPLE_STRUCTURED,
        recipe_id="id-abc",
        slug="banana-bread",
        config=_SAMPLE_CONFIG,
    )
    for ing in payload["recipeIngredient"]:
        uuid.UUID(ing["referenceId"])  # raises ValueError if invalid
