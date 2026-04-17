"""Shared pytest fixtures."""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Return a path for an ephemeral SQLite DB for a single test."""
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests never accidentally hit the real Anthropic API."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-do-not-use")
