print("UTILITY VERSION = 2025-12-19 18:30 (fingerprint)", __file__)

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    """
    Loads environment variables from .env if it exists.
    Local dev only. For cloud deploy, set env vars in the platform's secrets.
    """
    env_path = ROOT / ".env"
    if env_path.exists():
        from dotenv import load_dotenv  # <-- import inside function (guaranteed)
        load_dotenv(env_path)


def get_api_key() -> Optional[str]:
    """
    Returns the API key from environment variables, if present.
    """
    return os.getenv("OPENAI_API_KEY")


# ----------------------------
# Personas
# ----------------------------
def load_personas(personas_path: Path) -> Any:
    """
    Loads personas from JSON.

    Supported formats:
      1) {"personas": [ ... ]}
      2) [ ... ] (direct list of personas)

    Returns:
      - dict or list (we normalize in app.py)
    """
    with open(personas_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------
# Reporting helpers
# ----------------------------
def ensure_reports_dir() -> Path:
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def timestamp() -> str:
    """
    Timestamp used for filenames / run IDs.
    Example: 20251219_170455
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_json(obj: dict, out_path: Path) -> Path:
    """
    Saves JSON to a specific path.
    Returns the out_path for convenience.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    return out_path


def append_markdown(md_path: Path, text: str) -> Path:
    """
    Appends markdown text to a .md file.
    Returns the md_path for convenience.
    """
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n\n")
    return md_path
