from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .models import Commitment, Preferences, ScheduleBlock, as_dict
from .scheduler import schedule_tasks
from .storage import JsonStore
from .validator import hard_errors, validate_blocks


def get_preferences(store: JsonStore) -> dict[str, Any]:
    return store.load("preferences")


def save_preferences(store: JsonStore, preferences: Preferences) -> None:
    store.save("preferences", as_dict(preferences))


def add_commitment(store: JsonStore, commitment: Commitment) -> None:
    rows = store.load("commitments")
    rows.append(as_dict(commitment))
    store.save("commitments", rows)


def propose_day(store: JsonStore, target: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Any]]:
    raw_preferences = get_preferences(store)
    preferences = Preferences(**raw_preferences)
    fixed = [
        ScheduleBlock(
            id=row["id"],
            date=row["date"],
            start=row["start"],
            end=row["end"],
            title=row["title"],
            category=row.get("category", "commitment"),
            fixed=True,
            notes=row.get("notes", ""),
        )
        for row in store.load("commitments") if row.get("date") == target.isoformat()
    ]
    current = [
        ScheduleBlock(**row) for row in store.load("schedule") if row.get("date") == target.isoformat()
    ]
    blocks, unscheduled = schedule_tasks(
        target,
        store.load("study_goals"),
        preferences,
        fixed + [block for block in current if not block.fixed],
    )
    issues = validate_blocks(blocks, store.load("study_goals"), {row["id"] for row in store.load("subjects")})
    return [as_dict(block) for block in blocks], unscheduled, issues


def approve_day(store: JsonStore, blocks: list[dict[str, Any]], target: date) -> None:
    existing = [row for row in store.load("schedule") if row.get("date") != target.isoformat()]
    store.save("schedule", existing + blocks)
    history = store.load("history")
    history.append({"timestamp": datetime.now().astimezone().isoformat(), "date": target.isoformat(), "blocks": blocks})
    store.save("history", history)


def current_or_next(store: JsonStore, target: date, now: datetime | None = None) -> tuple[str, dict[str, Any] | None]:
    current_time = (now or datetime.now()).strftime("%H:%M")
    blocks = sorted(
        [row for row in store.load("schedule") if row.get("date") == target.isoformat()],
        key=lambda row: row["start"],
    )
    for block in blocks:
        if block["start"] <= current_time < block["end"]:
            return "current", block
        if block["start"] > current_time:
            return "next", block
    return "none", None
