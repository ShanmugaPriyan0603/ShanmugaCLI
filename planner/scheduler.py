from __future__ import annotations

from datetime import date
from typing import Any

from .models import Preferences, ScheduleBlock, StudyTask, new_id
from .time_utils import add_minutes, minutes_between


def _same_day_minutes(start: str, end: str) -> int:
    start_minutes = int(start[:2]) * 60 + int(start[3:])
    end_minutes = int(end[:2]) * 60 + int(end[3:])
    return end_minutes - start_minutes


def schedule_tasks(
    target: date,
    tasks: list[dict[str, Any]],
    preferences: Preferences,
    occupied: list[ScheduleBlock],
) -> tuple[list[ScheduleBlock], list[dict[str, Any]]]:
    cursor = preferences.wake_time
    end_of_day = preferences.sleep_time
    available = []
    for task in sorted(tasks, key=lambda item: (-int(item.get("priority", 3)), item.get("deadline") or "9999")):
        duration = max(1, int(task.get("estimated_minutes", 30)))
        if int(task.get("actual_minutes", 0)) >= duration or task.get("status") in {"completed", "cancelled"}:
            continue
        if _same_day_minutes(cursor, end_of_day) < duration:
            available.append(task)
            continue
        block = ScheduleBlock(
            id=new_id(),
            date=target.isoformat(),
            start=cursor,
            end=add_minutes(cursor, duration),
            title=task.get("description") or task.get("topic") or "Study task",
            category="study",
            subject_id=task.get("subject_id"),
            topic=task.get("topic", ""),
            task_id=task.get("id"),
            priority=int(task.get("priority", 3)),
        )
        available.append(None)
        occupied.append(block)
        next_cursor = add_minutes(block.end, preferences.break_minutes)
        if _same_day_minutes(next_cursor, end_of_day) < 0:
            cursor = end_of_day
        else:
            cursor = next_cursor
    return occupied, [task for task in available if task is not None]
