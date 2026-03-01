"""Shared fixtures for the mealie-cookbook-scanner test suite."""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import AppConfig


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_config() -> AppConfig:
    """A fully-populated AppConfig for use in unit tests."""
    return AppConfig(
        mealie_url="http://mealie.test",
        mealie_token="test-token-123",
        llm_provider="anthropic",
        llm_key="sk-ant-test-key",
        mealie_user_id="user-uuid-1",
        mealie_household_id="household-uuid-1",
        mealie_group_id="group-uuid-1",
    )


@pytest.fixture()
def config_file(tmp_path: Path, sample_config: AppConfig) -> Path:
    """Write sample config to a temp file and point CONFIG_PATH at it."""
    import app.config as cfg_module

    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "mealie_url": sample_config.mealie_url,
                "mealie_token": sample_config.mealie_token,
                "llm_provider": sample_config.llm_provider,
                "llm_key": sample_config.llm_key,
                "mealie_user_id": sample_config.mealie_user_id,
                "mealie_household_id": sample_config.mealie_household_id,
                "mealie_group_id": sample_config.mealie_group_id,
            }
        )
    )
    original = cfg_module.CONFIG_PATH
    cfg_module.CONFIG_PATH = cfg
    yield cfg
    cfg_module.CONFIG_PATH = original


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------


def _make_jpeg(width: int = 200, height: int = 100, color: tuple = (120, 80, 60)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def small_jpeg() -> bytes:
    return _make_jpeg(200, 100)


@pytest.fixture()
def large_jpeg() -> bytes:
    """JPEG larger than 10 MB (raw pixel data, not compressed — use size mock for upload tests)."""
    # Create a JPEG that when re-read is large; use a big image for that
    return _make_jpeg(5000, 5000)


# ---------------------------------------------------------------------------
# ASGI test client
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(config_file):  # noqa: F811  # depends on config_file so load_config works
    from app.main import app

    with TestClient(app) as c:
        yield c
