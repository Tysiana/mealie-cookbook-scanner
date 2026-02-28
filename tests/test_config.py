"""Unit tests for app.config — load/save and AppConfig dataclass."""

import json
from pathlib import Path

import pytest

import app.config as cfg_module
from app.config import AppConfig, load_config, save_config


_FULL_DATA = {
    "mealie_url": "http://mealie.test",
    "mealie_token": "tok",
    "anthropic_key": "key",
    "mealie_user_id": "u1",
    "mealie_household_id": "h1",
    "mealie_group_id": "g1",
}


def test_load_config_returns_none_when_file_missing(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "nonexistent.json"
    assert load_config() is None


def test_load_config_returns_none_on_missing_field(tmp_path: Path):
    cfg = tmp_path / "config.json"
    incomplete = {k: v for k, v in _FULL_DATA.items() if k != "anthropic_key"}
    cfg.write_text(json.dumps(incomplete))
    cfg_module.CONFIG_PATH = cfg
    assert load_config() is None


def test_load_config_returns_none_on_invalid_json(tmp_path: Path):
    cfg = tmp_path / "config.json"
    cfg.write_text("{not valid json")
    cfg_module.CONFIG_PATH = cfg
    assert load_config() is None


def test_load_config_returns_appconfig(tmp_path: Path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_FULL_DATA))
    cfg_module.CONFIG_PATH = cfg
    result = load_config()
    assert isinstance(result, AppConfig)
    assert result.mealie_url == "http://mealie.test"
    assert result.mealie_token == "tok"


def test_save_and_reload(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "sub" / "config.json"
    save_config(_FULL_DATA)
    result = load_config()
    assert result is not None
    assert result.anthropic_key == "key"


def test_is_configured_false_when_missing(tmp_path: Path):
    cfg_module.CONFIG_PATH = tmp_path / "nope.json"
    assert not cfg_module.is_configured()


def test_is_configured_true_when_present(tmp_path: Path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_FULL_DATA))
    cfg_module.CONFIG_PATH = cfg
    assert cfg_module.is_configured()
