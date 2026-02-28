import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path("/app/config/config.json")

_REQUIRED_FIELDS = [
    "mealie_url",
    "mealie_token",
    "anthropic_key",
    "mealie_user_id",
    "mealie_household_id",
    "mealie_group_id",
]


@dataclass
class AppConfig:
    mealie_url: str
    mealie_token: str
    anthropic_key: str
    mealie_user_id: str
    mealie_household_id: str
    mealie_group_id: str


def load_config() -> Optional[AppConfig]:
    """Load and return app config from disk, or None if missing/incomplete."""
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        if not all(data.get(k) for k in _REQUIRED_FIELDS):
            return None
        return AppConfig(
            mealie_url=data["mealie_url"],
            mealie_token=data["mealie_token"],
            anthropic_key=data["anthropic_key"],
            mealie_user_id=data["mealie_user_id"],
            mealie_household_id=data["mealie_household_id"],
            mealie_group_id=data["mealie_group_id"],
        )
    except (KeyError, json.JSONDecodeError):
        return None


def save_config(data: dict) -> None:
    """Persist config dict to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def is_configured() -> bool:
    """Return True if a complete config exists on disk."""
    return load_config() is not None
