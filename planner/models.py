from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


@dataclass
class Topic:
    name: str
    estimated_hours: float = 0.0
    difficulty: int = 3
    importance: int = 3
    status: str = "not_started"
    completed_at: str | None = None
    revision_count: int = 0
    last_studied: str | None = None
    next_revision: str | None = None
    notes: str = ""


@dataclass
class Unit:
    name: str
    number: int = 1
    topics: list[Topic] = field(default_factory=list)


@dataclass
class Subject:
    id: str = field(default_factory=new_id)
    name: str = ""
    abbreviation: str = ""
    units: list[Unit] = field(default_factory=list)
    exam_date: str | None = None
    priority: int = 3
    difficulty: int = 3
    confidence: int = 3
    estimated_remaining_hours: float = 0.0
    completed_hours: float = 0.0
    preferred_session_minutes: int = 45
    revision_intervals: list[int] = field(default_factory=lambda: [1, 3, 7, 14, 30])
    notes: str = ""
    archived: bool = False
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class StudyTask:
    id: str = field(default_factory=new_id)
    subject_id: str | None = None
    topic: str = ""
    description: str = ""
    deadline: str | None = None
    estimated_minutes: int = 30
    priority: int = 3
    difficulty: int = 3
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    planned_minutes: int = 0
    actual_minutes: int = 0
    completed_at: str | None = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class StudyLog:
    id: str = field(default_factory=new_id)
    date: str = field(default_factory=lambda: datetime.now().date().isoformat())
    subject_id: str | None = None
    topic: str = ""
    task_id: str | None = None
    minutes: int = 0
    understanding: int = 3
    completed: bool = False
    notes: str = ""


@dataclass
class ScheduleBlock:
    id: str = field(default_factory=new_id)
    date: str = ""
    start: str = ""
    end: str = ""
    title: str = ""
    category: str = "study"
    subject_id: str | None = None
    topic: str = ""
    task_id: str | None = None
    status: str = "planned"
    priority: int = 3
    fixed: bool = False
    source: str = "local"
    notes: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class Commitment:
    id: str = field(default_factory=new_id)
    date: str = ""
    start: str = ""
    end: str = ""
    title: str = ""
    category: str = "commitment"
    fixed: bool = True
    notes: str = ""


@dataclass
class Preferences:
    wake_time: str = "07:00"
    sleep_time: str = "23:00"
    college_start: str | None = None
    college_end: str | None = None
    commute_minutes: int = 0
    meal_minutes: int = 30
    exercise_minutes: int = 0
    preferred_study_hours: float = 4.0
    max_continuous_minutes: int = 90
    break_every_minutes: int = 45
    break_minutes: int = 10
    gaming_minutes: int = 0
    reading_minutes: int = 0
    relaxation_minutes: int = 30
    preferred_session_minutes: int = 45
    days_off: list[str] = field(default_factory=list)
    weekly_target_hours: float = 20.0


def as_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
