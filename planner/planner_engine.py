from __future__ import annotations

from datetime import date
from typing import Any

from .day_engine import propose_day
from .gemini_client import GeminiPlanner
from .storage import JsonStore


def build_context(store: JsonStore, target: date) -> dict[str, Any]:
    return {
        "date": target.isoformat(),
        "preferences": store.load("preferences"),
        "subjects": store.load("subjects"),
        "pending_tasks": [
            task for task in store.load("study_goals")
            if task.get("status") not in {"completed", "cancelled"}
        ],
        "commitments": [
            item for item in store.load("commitments")
            if item.get("date") == target.isoformat()
        ],
    }


def local_proposal(store: JsonStore, target: date) -> tuple[list[dict], list[dict], list]:
    return propose_day(store, target)


def ai_proposal(store: JsonStore, target: date) -> dict[str, Any]:
    return GeminiPlanner().propose(build_context(store, target))
