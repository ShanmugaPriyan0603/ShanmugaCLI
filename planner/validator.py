from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .models import ScheduleBlock, StudyTask
from .time_utils import minutes_between, overlaps, parse_date, parse_time


@dataclass
class Issue:
    level: str
    code: str
    message: str


def validate_blocks(
    blocks: Iterable[ScheduleBlock],
    tasks: Iterable[StudyTask] = (),
    subject_ids: set[str] | None = None,
) -> list[Issue]:
    items = list(blocks)
    issues: list[Issue] = []
    seen: set[str] = set()
    task_ids = {task.id for task in tasks}
    for block in items:
        if block.id in seen:
            issues.append(Issue("error", "duplicate_id", f"Duplicate block id: {block.id}"))
        seen.add(block.id)
        try:
            parse_date(block.date)
            start, end = parse_time(block.start), parse_time(block.end)
            if start >= end:
                issues.append(Issue("error", "invalid_time", f"{block.title}: end must follow start"))
        except ValueError:
            issues.append(Issue("error", "invalid_datetime", f"{block.title}: invalid date or time"))
        if block.subject_id and subject_ids is not None and block.subject_id not in subject_ids:
            issues.append(Issue("error", "invalid_subject", f"{block.title}: unknown subject"))
        if block.task_id and block.task_id not in task_ids:
            issues.append(Issue("error", "invalid_task", f"{block.title}: unknown task"))
        if block.start and block.end and minutes_between(block.start, block.end) <= 0:
            issues.append(Issue("error", "nonpositive_duration", f"{block.title}: duration is not positive"))
    for index, first in enumerate(items):
        for second in items[index + 1:]:
            if first.date == second.date and overlaps(first.start, first.end, second.start, second.end):
                level = "error" if first.fixed or second.fixed else "warning"
                issues.append(Issue(level, "overlap", f"{first.title} overlaps {second.title}"))
    return issues


def hard_errors(issues: Iterable[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.level == "error"]
