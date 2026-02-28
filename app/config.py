import json
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path("/app/config/config.json")


def load_config() -> Optional[dict]:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def is_configured() -> bool:
    config = load_config()
    if not config:
        return False
    required = [
        "mealie_url",
        "mealie_token",
        "anthropic_key",
        "mealie_user_id",
        "mealie_household_id",
        "mealie_group_id",
    ]
    return all(config.get(k) for k in required)
