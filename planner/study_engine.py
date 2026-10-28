from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .models import StudyLog, StudyTask, Subject, Topic, Unit, as_dict, now_iso
from .storage import JsonStore


def subjects(store: JsonStore) -> list[dict[str, Any]]:
    return store.load("subjects")


def add_subject(store: JsonStore, subject: Subject) -> Subject:
    rows = subjects(store)
    rows.append(as_dict(subject))
    store.save("subjects", rows)
    return subject


def add_unit(store: JsonStore, subject_id: str, unit: Unit) -> None:
    rows = subjects(store)
    subject = next(row for row in rows if row["id"] == subject_id)
    subject.setdefault("units", []).append(as_dict(unit))
    subject["updated_at"] = now_iso()
    store.save("subjects", rows)


def add_topic(store: JsonStore, subject_id: str, unit_number: int, topic: Topic) -> None:
    rows = subjects(store)
    subject = next(row for row in rows if row["id"] == subject_id)
    unit = next(unit for unit in subject.setdefault("units", []) if unit["number"] == unit_number)
    unit.setdefault("topics", []).append(as_dict(topic))
    subject["updated_at"] = now_iso()
    store.save("subjects", rows)


def add_task(store: JsonStore, task: StudyTask) -> None:
    rows = store.load("study_goals")
    rows.append(as_dict(task))
    store.save("study_goals", rows)


def log_session(store: JsonStore, log: StudyLog) -> None:
    logs = store.load("progress")
    logs.append(as_dict(log))
    store.save("progress", logs)
    if log.subject_id:
        rows = subjects(store)
        for subject in rows:
            if subject["id"] == log.subject_id:
                subject["completed_hours"] = float(subject.get("completed_hours", 0)) + log.minutes / 60
                subject["updated_at"] = now_iso()
        store.save("subjects", rows)
    if log.task_id:
        tasks = store.load("study_goals")
        for task in tasks:
            if task["id"] == log.task_id:
                task["actual_minutes"] = int(task.get("actual_minutes", 0)) + log.minutes
        store.save("study_goals", tasks)


def complete_task(store: JsonStore, task_id: str) -> None:
    tasks = store.load("study_goals")
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            task["completed_at"] = now_iso()
            task["updated_at"] = now_iso()
            store.save("study_goals", tasks)
            return
    raise ValueError(f"Unknown task: {task_id}")


def progress(store: JsonStore) -> list[dict[str, Any]]:
    result = []
    for subject in subjects(store):
        topics = [topic for unit in subject.get("units", []) for topic in unit.get("topics", [])]
        completed = sum(topic.get("status") == "completed" for topic in topics)
        result.append({
            "subject": subject["name"],
            "topics_completed": completed,
            "topics_total": len(topics),
            "percentage": round(completed / len(topics) * 100, 1) if topics else 0.0,
            "completed_hours": subject.get("completed_hours", 0),
        })
    return result


def revision_due(store: JsonStore, on: date | None = None) -> list[dict[str, Any]]:
    today = on or date.today()
    due = []
    for subject in subjects(store):
        for unit in subject.get("units", []):
            for topic in unit.get("topics", []):
                next_revision = topic.get("next_revision")
                if next_revision and date.fromisoformat(next_revision) <= today:
                    due.append({"subject": subject["name"], "topic": topic["name"]})
    return due


def schedule_revision(topic: dict[str, Any], intervals: list[int], studied: date | None = None) -> None:
    current = studied or date.today()
    count = int(topic.get("revision_count", 0))
    topic["next_revision"] = (current + timedelta(days=intervals[min(count, len(intervals) - 1)])).isoformat()


def normalize_study_intake(
    intake: dict[str, Any],
    today: date | None = None,
) -> dict[str, Any]:
    """Validate AI extraction and derive values the model must not invent."""
    current = today or date.today()
    normalized: dict[str, Any] = {
        "subjects": [],
        "tasks": intake.get("tasks", []),
        "preferences": intake.get("preferences", {}),
        "assumptions": intake.get("assumptions", []),
        "missing_details": intake.get("missing_details", []),
        "extracted_at": datetime.now().astimezone().isoformat(),
    }
    if not isinstance(normalized["tasks"], list):
        raise ValueError("AI intake tasks must be a list.")
    for raw in intake.get("subjects", []):
        if not isinstance(raw, dict) or not str(raw.get("name", "")).strip():
            raise ValueError("AI intake contains a subject without a name.")
        exam_date = raw.get("exam_date")
        if exam_date:
            try:
                exam = date.fromisoformat(exam_date)
            except ValueError as exc:
                raise ValueError(f"Invalid exam date for {raw['name']}: {exam_date}") from exc
            days_left = (exam - current).days
        else:
            days_left = None
        units = []
        for index, unit in enumerate(raw.get("units", []), start=1):
            status = unit.get("status", "not_started")
            if status not in {"completed", "in_progress", "needs_revision", "not_started"}:
                status = "not_started"
            units.append({
                "number": int(unit.get("number", index)),
                "name": str(unit.get("name", "")).strip(),
                "status": status,
            })
        completed_units = sum(unit["status"] == "completed" for unit in units)
        total_units = len(units)
        normalized["subjects"].append({
            "name": str(raw["name"]).strip(),
            "abbreviation": str(raw.get("abbreviation", "")).strip(),
            "exam_date": exam_date,
            "days_left": days_left,
            "hours_left": days_left * 24 if days_left is not None else None,
            "total_units": total_units,
            "completed_units": completed_units,
            "remaining_units": max(0, total_units - completed_units),
            "priority": min(5, max(1, int(raw.get("priority", 3)))),
            "difficulty": min(5, max(1, int(raw.get("difficulty", 3)))),
            "confidence": min(5, max(1, int(raw.get("confidence", 3)))),
            "feeling": str(raw.get("feeling", "")).strip(),
            "estimated_remaining_hours": max(0.0, float(raw.get("estimated_remaining_hours", 0))),
            "units": units,
            "notes": str(raw.get("notes", "")).strip(),
        })
    return normalized


def save_study_intake(store: JsonStore, intake: dict[str, Any]) -> dict[str, int]:
    """Merge a normalized intake into subjects and study tasks without duplicates."""
    subject_rows = store.load("subjects")
    task_rows = store.load("study_goals")
    subject_ids: dict[str, str] = {}
    added_subjects = 0
    added_tasks = 0

    for extracted in intake["subjects"]:
        existing = next(
            (row for row in subject_rows if row["name"].casefold() == extracted["name"].casefold()),
            None,
        )
        if existing is None:
            subject = Subject(
                name=extracted["name"],
                abbreviation=extracted["abbreviation"],
                exam_date=extracted["exam_date"],
                priority=extracted["priority"],
                difficulty=extracted["difficulty"],
                confidence=extracted["confidence"],
                estimated_remaining_hours=extracted["estimated_remaining_hours"],
                notes=extracted["notes"],
            )
            existing = as_dict(subject)
            subject_rows.append(existing)
            added_subjects += 1
        else:
            for key in (
                "abbreviation",
                "exam_date",
                "priority",
                "difficulty",
                "confidence",
                "estimated_remaining_hours",
                "notes",
            ):
                value = extracted.get(key)
                if value not in (None, "", 0, 0.0):
                    existing[key] = value
            existing["updated_at"] = now_iso()
        subject_ids[extracted["name"].casefold()] = existing["id"]

        for unit in extracted["units"]:
            units = existing.setdefault("units", [])
            current_unit = next(
                (item for item in units if item.get("number") == unit["number"]),
                None,
            )
            if current_unit is None:
                units.append({
                    "number": unit["number"],
                    "name": unit["name"],
                    "topics": [],
                })
                current_unit = units[-1]
            if unit["name"]:
                current_unit["name"] = unit["name"]
            if unit["status"] != "not_started":
                current_unit.setdefault("topics", [])
                current_unit["status"] = unit["status"]

    for task in intake["tasks"]:
        subject_id = subject_ids.get(str(task.get("subject_name", "")).casefold())
        description = str(task.get("description", "")).strip()
        if not description:
            continue
        duplicate = next(
            (
                row for row in task_rows
                if row.get("description", "").casefold() == description.casefold()
                and row.get("subject_id") == subject_id
                and row.get("status") not in {"cancelled", "completed"}
            ),
            None,
        )
        if duplicate is None:
            task_rows.append(as_dict(StudyTask(
                subject_id=subject_id,
                description=description,
                deadline=task.get("deadline"),
                estimated_minutes=max(1, int(task.get("estimated_minutes", 30))),
                priority=min(5, max(1, int(task.get("priority", 3)))),
            )))
            added_tasks += 1

    store.save("subjects", subject_rows)
    store.save("study_goals", task_rows)
    return {"subjects_added": added_subjects, "tasks_added": added_tasks}
