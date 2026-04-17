"""Environment configuration for the CV engine."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# Load .env from the server/ directory if present. Never errors if missing.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


DEFAULT_EXTRACT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_SCORE_MODEL = "claude-sonnet-4-6"


class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    anthropic_api_key: str
    db_path: Path
    extract_model: str
    score_model: str
    score_temperature: float
    server_root: Path


def load_config() -> Config:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    server_root = Path(__file__).resolve().parent.parent
    default_db = server_root / "cv_engine.db"
    db_path = Path(os.environ.get("CV_ENGINE_DB_PATH", default_db))

    return Config(
        anthropic_api_key=api_key,
        db_path=db_path,
        extract_model=os.environ.get("CV_ENGINE_EXTRACT_MODEL", DEFAULT_EXTRACT_MODEL),
        score_model=os.environ.get("CV_ENGINE_SCORE_MODEL", DEFAULT_SCORE_MODEL),
        score_temperature=float(os.environ.get("CV_ENGINE_SCORE_TEMPERATURE", "0")),
        server_root=server_root,
    )
