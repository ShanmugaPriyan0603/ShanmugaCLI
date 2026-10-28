from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
LOCAL_ENV_FILE = ROOT / ".env.local"
DEFAULT_MODEL = "gemini-3.8-flash"
DATA_FILES = (
    "preferences",
    "subjects",
    "study_goals",
    "schedule",
    "progress",
    "commitments",
    "history",
)


def model_name() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def api_key() -> str | None:
    configured = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if configured:
        return configured

    if not LOCAL_ENV_FILE.is_file():
        return None

    try:
        for raw_line in LOCAL_ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}:
                return value.strip().strip("\"'")
    except OSError:
        return None

    return None


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
