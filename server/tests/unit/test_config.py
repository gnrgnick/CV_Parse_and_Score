from __future__ import annotations

from pathlib import Path

import pytest

from cv_engine.config import Config, load_config


def test_load_config_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(tmp_path / "cv_engine.db"))
    monkeypatch.delenv("CV_ENGINE_EXTRACT_MODEL", raising=False)
    monkeypatch.delenv("CV_ENGINE_SCORE_MODEL", raising=False)

    cfg = load_config()

    assert cfg.anthropic_api_key == "sk-test"
    assert cfg.db_path == tmp_path / "cv_engine.db"
    assert cfg.extract_model == "claude-haiku-4-5-20251001"
    assert cfg.score_model == "claude-sonnet-4-6"
    assert cfg.score_temperature == 0.0


def test_load_config_model_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("CV_ENGINE_DB_PATH", str(tmp_path / "cv_engine.db"))
    monkeypatch.setenv("CV_ENGINE_EXTRACT_MODEL", "claude-haiku-4-5")
    monkeypatch.setenv("CV_ENGINE_SCORE_MODEL", "claude-opus-4-7")

    cfg = load_config()

    assert cfg.extract_model == "claude-haiku-4-5"
    assert cfg.score_model == "claude-opus-4-7"


def test_load_config_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        load_config()


def test_config_is_frozen() -> None:
    cfg = Config(
        anthropic_api_key="x",
        db_path=Path("/tmp/x.db"),
        extract_model="m",
        score_model="s",
        score_temperature=0.0,
        server_root=Path("/tmp"),
    )
    with pytest.raises(Exception):  # pydantic raises ValidationError on mutation
        cfg.anthropic_api_key = "y"  # type: ignore[misc]
