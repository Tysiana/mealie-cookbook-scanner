"""Integration tests for GET/POST /api/config and GET /api/health."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

import app.config as cfg_module
from app.config import AppConfig


_FULL_CONFIG = {
    "mealie_url": "http://mealie.test",
    "mealie_token": "tok",
    "anthropic_key": "key",
    "mealie_user_id": "u1",
    "mealie_household_id": "h1",
    "mealie_group_id": "g1",
}


@pytest.fixture()
def configured_client(tmp_path: Path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_FULL_CONFIG))
    cfg_module.CONFIG_PATH = cfg
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def unconfigured_client(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "none.json"
    from app.main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(configured_client):
    r = configured_client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /api/config
# ---------------------------------------------------------------------------


def test_get_config_returns_configured(configured_client):
    r = configured_client.get("/api/config")
    assert r.status_code == 200
    data = r.json()
    assert data["configured"] is True
    assert data["mealie_url"] == "http://mealie.test"
    assert data["mealie_token_set"] is True
    assert data["anthropic_key_set"] is True
    # Raw credentials must NOT be present
    assert "mealie_token" not in data
    assert "anthropic_key" not in data


def test_get_config_returns_unconfigured(unconfigured_client):
    r = unconfigured_client.get("/api/config")
    assert r.status_code == 200
    assert r.json() == {"configured": False}


# ---------------------------------------------------------------------------
# POST /api/config
# ---------------------------------------------------------------------------


def test_post_config_saves_on_success(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "config.json"
    from app.main import app

    fake_uuids = {
        "mealie_user_id": "uid",
        "mealie_household_id": "hhid",
        "mealie_group_id": "gid",
    }

    with patch("app.routes.config.fetch_user_info", new=AsyncMock(return_value=fake_uuids)):
        with TestClient(app) as client:
            r = client.post(
                "/api/config",
                json={
                    "mealie_url": "http://mealie.test/",
                    "mealie_token": "tok",
                    "anthropic_key": "key",
                },
            )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    saved = json.loads(cfg_module.CONFIG_PATH.read_text())
    # Trailing slash stripped
    assert saved["mealie_url"] == "http://mealie.test"


def test_post_config_returns_400_on_mealie_error(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "config.json"
    from app.main import app

    with patch(
        "app.routes.config.fetch_user_info",
        new=AsyncMock(side_effect=Exception("connection refused")),
    ):
        with TestClient(app) as client:
            r = client.post(
                "/api/config",
                json={
                    "mealie_url": "http://bad.host",
                    "mealie_token": "tok",
                    "anthropic_key": "key",
                },
            )
    assert r.status_code == 400
    assert "bad.host" in r.json()["detail"]
