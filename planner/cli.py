from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from .day_engine import add_commitment, approve_day, current_or_next, propose_day, save_preferences
from .errors import PlannerError
from .gemini_client import GeminiPlanner
from .models import Commitment, Preferences, ScheduleBlock, StudyLog, StudyTask, Subject, Topic, Unit, as_dict
from .planner_engine import ai_proposal
from .renderer import box, schedule_text
from .storage import JsonStore
from .study_engine import (
    add_subject,
    add_task,
    add_topic,
    add_unit,
    complete_task,
    log_session,
    normalize_study_intake,
    progress,
    revision_due,
    save_study_intake,
)
from .validator import validate_blocks


def _id_or_name(rows: list[dict], value: str) -> str:
    for row in rows:
        if row.get("id") == value or row.get("name") == value:
            return row["id"]
    raise PlannerError(f"Unknown subject: {value}")


def study_help() -> str:
    return box("STUDY COMMANDS", [
        "study subjects",
        "study ask [free-form exam details]",
        "study subject NAME",
        "study add-subject NAME",
        "study archive ID",
        "study syllabus",
        "study add-unit ID",
        "study add-topic ID",
        "study add-task [ID]",
        "study tasks",
        "study complete ID",
        "study deadline",
        "study plan",
        "study log [MINUTES]",
        "study progress",
        "study revision",
        "study stats",
        "study export",
        "study import FILE",
        "study help",
    ], width=76)


def day_help() -> str:
    return box("DAY COMMANDS", [
        "day plan [DATE]",
        "day plan --ai [DATE]",
        "day today",
        "day tomorrow",
        "day week",
        "day now",
        "day next",
        "day add",
        "day edit ID",
        "day done ID",
        "day skip ID",
        "day delete ID",
        "day replan",
        "day conflicts",
        "day commitments",
        "day preferences",
        "day history",
        "day stats",
        "day help",
    ], width=76)


def handle_study(args: list[str], store: JsonStore) -> int:
    command = args[0] if args else "dashboard"
    if command == "help":
        print(study_help())
    elif command == "ask":
        text = " ".join(args[1:]).strip()
        if not text:
            text = input("Describe your exams, subjects, progress, feelings, and constraints:\n> ").strip()
        if not text:
            raise PlannerError("No study details were provided.")
        extracted = GeminiPlanner().extract_study_intake(text, date.today().isoformat())
        normalized = normalize_study_intake(extracted)
        print(json.dumps(normalized, indent=2, ensure_ascii=False))
        if normalized["missing_details"]:
            print("\nMissing details:")
            for detail in normalized["missing_details"]:
                print(f"- {detail}")
        if input("\nSave this extracted data to the study planner? [y/N] ").strip().lower() != "y":
            print("Extraction discarded; no planner data was changed.")
            return 0
        counts = save_study_intake(store, normalized)
        print(
            f"Saved {counts['subjects_added']} new subject(s) and "
            f"{counts['tasks_added']} new task(s)."
        )
    elif command in {"subjects", "subject"}:
        rows = store.load("subjects")
        if command == "subject" and len(args) > 1:
            rows = [row for row in rows if row["id"] == args[1] or row["name"].lower() == args[1].lower()]
        print(box("SUBJECTS", [f"{row['name']}  {row['id']}  {row.get('exam_date') or 'no exam'}" for row in rows] or ["No subjects."]))
    elif command == "syllabus":
        rows = store.load("subjects")
        lines = []
        for subject in rows:
            lines.append(subject["name"])
            for unit in subject.get("units", []):
                lines.append(f"  Unit {unit.get('number', 1)}: {unit['name']}")
                lines.extend(f"    - {topic['name']} [{topic.get('status', 'not_started')}]" for topic in unit.get("topics", []))
        print(box("SYLLABUS", lines or ["No syllabus recorded."]))
    elif command == "add-subject":
        name = " ".join(args[1:]) or input("Subject name: ").strip()
        add_subject(store, Subject(name=name))
        print(f"Added subject: {name}")
    elif command == "archive":
        subject_id = args[1]
        rows = store.load("subjects")
        for row in rows:
            if row["id"] == subject_id or row["name"].lower() == subject_id.lower():
                row["archived"] = True
                store.save("subjects", rows)
                print("Subject archived.")
                break
        else:
            raise PlannerError(f"Unknown subject: {subject_id}")
    elif command == "add-unit":
        subject_id = args[1] if len(args) > 1 else input("Subject id: ")
        add_unit(store, subject_id, Unit(name=input("Unit name: "), number=int(input("Unit number: "))))
        print("Unit added.")
    elif command == "add-topic":
        subject_id = args[1] if len(args) > 1 else input("Subject id: ")
        add_topic(store, subject_id, int(input("Unit number: ")), Topic(name=input("Topic name: ")))
        print("Topic added.")
    elif command == "add-task":
        subject_id = args[1] if len(args) > 1 else None
        add_task(store, StudyTask(subject_id=subject_id, description=input("Task: "), estimated_minutes=int(input("Minutes: "))))
        print("Task added.")
    elif command == "tasks":
        rows = store.load("study_goals")
        print(box("STUDY TASKS", [f"{row['id']}  {row['status']:10} {row['description']}" for row in rows] or ["No tasks."]))
    elif command in {"complete", "complete-task"}:
        complete_task(store, args[1])
        print("Task completed.")
    elif command == "deadline":
        rows = [
            row for row in store.load("study_goals")
            if row.get("deadline") and row.get("status") not in {"completed", "cancelled"}
        ]
        print(box("DEADLINES", [f"{row['deadline']}  {row['description']}" for row in sorted(rows, key=lambda row: row["deadline"])] or ["No upcoming deadlines."]))
    elif command == "plan":
        rows = [row for row in store.load("study_goals") if row.get("status") not in {"completed", "cancelled"}]
        print(box("STUDY PLAN", [f"{row.get('deadline') or 'no deadline'}  {row['description']} ({row.get('estimated_minutes', 0)}m)" for row in rows] or ["No pending study tasks."]))
    elif command == "log":
        minutes = int(args[1]) if len(args) > 1 else int(input("Minutes studied: "))
        subject = input("Subject id (optional): ").strip() or None
        log_session(store, StudyLog(minutes=minutes, subject_id=subject, topic=input("What did you study? ")))
        print("Study session logged.")
    elif command in {"progress", "stats"}:
        print(box("STUDY PROGRESS", [f"{row['subject']}: {row['percentage']}% ({row['topics_completed']}/{row['topics_total']} topics), {row['completed_hours']}h" for row in progress(store)] or ["No subjects."]))
    elif command == "revision":
        print(box("REVISION DUE", [f"{row['subject']}: {row['topic']}" for row in revision_due(store)] or ["Nothing due."]))
    elif command == "export":
        print(json.dumps(store.export_all(), indent=2))
    elif command == "import":
        if len(args) < 2:
            raise PlannerError("Usage: study import FILE")
        source = Path(args[1]).resolve()
        if not source.is_file():
            raise PlannerError(f"Import file not found: {source}")
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PlannerError("Import must contain an object keyed by data file name.")
        if input("Import will replace matching planner data. Continue? [y/N] ").strip().lower() != "y":
            print("Import cancelled.")
            return 0
        for name, value in payload.items():
            if name in {"preferences", "subjects", "study_goals", "schedule", "progress", "commitments", "history"}:
                store.save(name, value)
        print("Planner data imported.")
    else:
        print(study_help())
    return 0


def handle_day(args: list[str], store: JsonStore) -> int:
    command = args[0] if args else "today"
    date_arg = next((value for value in args[1:] if value[:4].isdigit()), None)
    target = date.fromisoformat(date_arg) if date_arg else date.today()
    if command == "help":
        print(day_help())
    elif command in {"today", "tomorrow"}:
        target = date.today() if command == "today" else date.today().fromordinal(date.today().toordinal() + 1)
        print(schedule_text([row for row in store.load("schedule") if row["date"] == target.isoformat()]))
    elif command == "plan":
        if "--ai" in args:
            proposal = ai_proposal(store, target)
            blocks = []
            for raw in proposal.get("blocks", []):
                block = ScheduleBlock(
                    date=raw.get("date", target.isoformat()),
                    start=raw["start"],
                    end=raw["end"],
                    title=raw["title"],
                    category=raw.get("category", "study"),
                    subject_id=raw.get("subject_id"),
                    topic=raw.get("topic", ""),
                    task_id=raw.get("task_id"),
                    fixed=bool(raw.get("fixed", False)),
                    source="gemini",
                )
                blocks.append(block)
            issues = validate_blocks(
                blocks,
                store.load("study_goals"),
                {row["id"] for row in store.load("subjects")},
            )
            blocks = [as_dict(block) for block in blocks]
            unscheduled = proposal.get("unscheduled_tasks", [])
            print("AI proposal validated locally.")
        else:
            blocks, unscheduled, issues = propose_day(store, target)
            print("Local deterministic proposal.")
        print(schedule_text(blocks))
        print(f"\nUnscheduled tasks: {len(unscheduled)}")
        for issue in issues:
            print(f"{issue.level.upper()}: {issue.message}")
        if not any(issue.level == "error" for issue in issues) and input("\nApply these changes? [y/N] ").strip().lower() == "y":
            approve_day(store, blocks, target)
            print("Plan approved and saved.")
        else:
            print("Plan preview discarded; approved schedule unchanged.")
    elif command in {"now", "next"}:
        kind, block = current_or_next(store, date.today())
        print(f"{kind}: {block['title']} ({block['start']}-{block['end']})" if block else "No activity scheduled.")
    elif command == "add":
        add_commitment(store, Commitment(date=target.isoformat(), start=input("Start (HH:MM): "), end=input("End (HH:MM): "), title=input("Title: ")))
        print("Commitment added.")
    elif command == "commitments":
        print(schedule_text(store.load("commitments")))
    elif command == "preferences":
        current = Preferences(**store.load("preferences"))
        for field in ("wake_time", "sleep_time", "preferred_study_hours", "max_continuous_minutes"):
            value = input(f"{field} [{getattr(current, field)}]: ").strip()
            if value:
                setattr(current, field, type(getattr(current, field))(value))
        save_preferences(store, current)
        print("Preferences saved.")
    elif command == "history":
        print(json.dumps(store.load("history"), indent=2))
    elif command == "week":
        start = date.today()
        end = start.toordinal() + 7
        rows = [
            row for row in store.load("schedule")
            if start.toordinal() <= date.fromisoformat(row["date"]).toordinal() < end
        ]
        print(schedule_text(rows))
    elif command in {"done", "skip"}:
        if len(args) < 2:
            raise PlannerError(f"Usage: day {command} BLOCK_ID")
        rows = store.load("schedule")
        for row in rows:
            if row["id"] == args[1]:
                row["status"] = "completed" if command == "done" else "skipped"
                row["updated_at"] = datetime.now().astimezone().isoformat()
                store.save("schedule", rows)
                print(f"Block marked {row['status']}.")
                break
        else:
            raise PlannerError(f"Unknown schedule block: {args[1]}")
    elif command == "edit":
        if len(args) < 2:
            raise PlannerError("Usage: day edit BLOCK_ID")
        rows = store.load("schedule")
        for row in rows:
            if row["id"] == args[1]:
                title = input(f"Title [{row['title']}]: ").strip()
                if title:
                    row["title"] = title
                store.save("schedule", rows)
                print("Schedule block updated.")
                break
        else:
            raise PlannerError(f"Unknown schedule block: {args[1]}")
    elif command == "delete":
        if len(args) < 2:
            raise PlannerError("Usage: day delete BLOCK_ID")
        if input("Delete this schedule block? [y/N] ").strip().lower() != "y":
            print("Deletion cancelled.")
            return 0
        rows = [row for row in store.load("schedule") if row["id"] != args[1]]
        store.save("schedule", rows)
        print("Schedule block deleted.")
    elif command == "stats":
        rows = store.load("schedule")
        total = sum(
            max(0, int(row["end"][:2]) * 60 + int(row["end"][3:]) -
                int(row["start"][:2]) * 60 - int(row["start"][3:]))
            for row in rows
        )
        print(box("DAY STATS", [f"Scheduled minutes: {total}", f"Blocks: {len(rows)}"]))
    elif command in {"conflicts", "replan"}:
        blocks, _, issues = propose_day(store, target)
        print("\n".join(f"{issue.level.upper()}: {issue.message}" for issue in issues) or "No conflicts.")
    else:
        print(day_help())
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="planner", add_help=False)
    parser.add_argument("area", choices=["study", "day"])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    namespace = parser.parse_args(argv)
    try:
        return handle_study(namespace.command, JsonStore()) if namespace.area == "study" else handle_day(namespace.command, JsonStore())
    except (PlannerError, ValueError, IndexError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
