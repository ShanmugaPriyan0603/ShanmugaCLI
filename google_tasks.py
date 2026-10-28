# ============================================
#           SHANMUGA CLI - GOOGLE TASKS
# ============================================

import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# ============================================
#                 SETTINGS
# ============================================

BASE_DIR = r"C:\Users\shanm\ShanmugaCLI"
GOOGLE_DIR = os.path.join(BASE_DIR, "google")
TOKEN_FILE = os.path.join(GOOGLE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/tasks"
]


# ============================================
#                  COLORS
# ============================================

RESET = "\033[0m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
WHITE = "\033[97m"
GRAY = "\033[90m"


def color(text, colour):
    return f"{colour}{text}{RESET}"


# ============================================
#              GOOGLE CONNECTION
# ============================================

def _run_google_authentication():
    auth_script = os.path.join(BASE_DIR, "google_auth.py")
    return subprocess.run(
        [sys.executable, auth_script],
        check=False
    ).returncode == 0


def get_tasks_service():

    if not os.path.exists(TOKEN_FILE):

        print(
            color(
                "Google token not found.",
                RED
            )
        )

        print("Starting Google authentication...")

        if not _run_google_authentication():
            print(
                color(
                    "Google authentication could not be completed.",
                    RED
                )
            )
            return None

    try:

        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                if "invalid_grant" not in str(e):
                    raise

                print(
                    color(
                        "Google token expired or revoked. Starting authentication again.",
                        YELLOW
                    )
                )

                os.remove(TOKEN_FILE)
                if not _run_google_authentication():
                    print(
                        color(
                            "Google authentication could not be completed.",
                            RED
                        )
                    )
                    return None

                return get_tasks_service()

        if not creds.valid:

            print(
                color(
                    "Google authentication is invalid.",
                    RED
                )
            )

            print(
                "Run your Google authentication script again."
            )

            return None

        return build(
            "tasks",
            "v1",
            credentials=creds
        )

    except Exception as e:

        print(
            color(
                f"Google Tasks connection failed: {e}",
                RED
            )
        )

        return None


# ============================================
#                BOX HELPERS
# ============================================

BOX_WIDTH = 58


def box_line(text="", colour=WHITE):

    if len(text) > BOX_WIDTH - 4:
        text = text[:BOX_WIDTH - 4]

    padding = BOX_WIDTH - 4 - len(text)

    print(
        color("│  ", MAGENTA)
        + color(text, colour)
        + " " * padding
        + color("  │", MAGENTA)
    )


def box_top():
    print(
        color(
            "╭" + "─" * BOX_WIDTH + "╮",
            MAGENTA
        )
    )


def box_middle():
    print(
        color(
            "├" + "─" * BOX_WIDTH + "┤",
            MAGENTA
        )
    )


def box_bottom():
    print(
        color(
            "╰" + "─" * BOX_WIDTH + "╯",
            MAGENTA
        )
    )


# ============================================
#                 DATE PARSER
# ============================================

def parse_date(text):

    text = text.strip()

    today = datetime.now().date()

    lowered = text.lower()

    if lowered == "today":
        return today

    if lowered == "tomorrow":
        return today + timedelta(days=1)

    if lowered == "yesterday":
        return today - timedelta(days=1)

    formats = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %B",
        "%d %b %Y",
        "%d %b",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                text,
                fmt
            )

            if "%Y" not in fmt:
                parsed = parsed.replace(
                    year=today.year
                )

            return parsed.date()

        except ValueError:
            continue

    # Weekday names
    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    if lowered in weekdays:

        current = today.weekday()
        target = weekdays[lowered]

        delta = (target - current) % 7

        return today + timedelta(
            days=delta
        )

    return None


# ============================================
#                TASK LISTS
# ============================================

def get_task_lists(service):

    response = service.tasklists().list(
        maxResults=100
    ).execute()

    return response.get(
        "items",
        []
    )


def get_named_lists(service):

    lists = get_task_lists(service)

    result = {}

    for task_list in lists:

        title = task_list.get(
            "title",
            ""
        )

        result[title.lower()] = task_list

    return result


def select_task_list(service):

    lists = get_task_lists(service)

    if not lists:

        print(
            color(
                "No Google Task lists found.",
                RED
            )
        )

        return None

    # Prefer the user's two known lists
    preferred = [
        "My Tasks",
        "College Work"
    ]

    ordered = []

    for name in preferred:

        for task_list in lists:

            if task_list.get(
                "title",
                ""
            ).lower() == name.lower():

                ordered.append(task_list)

    # Add any other lists afterwards
    for task_list in lists:

        if task_list not in ordered:

            ordered.append(task_list)

    print()

    box_top()
    box_line(
        "GOOGLE TASKS",
        MAGENTA
    )
    box_middle()

    for i, task_list in enumerate(
        ordered,
        1
    ):

        title = task_list.get(
            "title",
            "(Untitled list)"
        )

        box_line(
            f"{i}. {title}",
            CYAN
        )

    box_bottom()

    print()

    while True:

        choice = input(
            color(
                "Select list > ",
                CYAN
            )
        ).strip()

        try:

            index = int(choice)

            if 1 <= index <= len(ordered):

                return ordered[index - 1]

        except ValueError:
            pass

        print(
            color(
                "Invalid selection.",
                RED
            )
        )


def resolve_list(service, name):

    lists = get_named_lists(service)

    if not name:

        return select_task_list(service)

    lowered = name.lower()

    if lowered in (
        "my",
        "tasks",
        "my tasks"
    ):

        if "my tasks" in lists:
            return lists["my tasks"]

    if lowered in (
        "college",
        "college work"
    ):

        if "college work" in lists:
            return lists["college work"]

    # Exact list name
    if lowered in lists:

        return lists[lowered]

    print(
        color(
            f'Could not find task list "{name}".',
            RED
        )
    )

    return None


# ============================================
#                  TASKS
# ============================================

def get_tasks(
    service,
    task_list_id,
    show_completed=False
):

    tasks = []

    page_token = None

    while True:

        response = service.tasks().list(
            tasklist=task_list_id,
            showCompleted=show_completed,
            showHidden=True,
            maxResults=100,
            pageToken=page_token
        ).execute()

        tasks.extend(
            response.get(
                "items",
                []
            )
        )

        page_token = response.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return tasks


def format_due(task):

    due = task.get("due")

    if not due:
        return "NO DEADLINE"

    try:

        dt = datetime.fromisoformat(
            due.replace(
                "Z",
                "+00:00"
            )
        )

        return dt.astimezone().strftime(
            "%d %b %Y"
        )

    except Exception:

        return due[:10]


def display_task(
    task,
    index=None
):

    title = task.get(
        "title",
        "(No title)"
    )

    status = task.get(
        "status",
        "needsAction"
    )

    marker = "✓" if status == "completed" else "○"

    prefix = ""

    if index is not None:
        prefix = f"{index}. "

    print(
        color(
            f"  {prefix}{marker} {title}",
            GREEN if status == "completed" else WHITE
        )
    )

    notes = task.get(
        "notes"
    )

    if notes:

        first_line = notes.splitlines()[0]

        print(
            color(
                f"      {first_line}",
                GRAY
            )
        )

    due = format_due(task)

    if due != "NO DEADLINE":

        print(
            color(
                f"      Due: {due}",
                YELLOW
            )
        )


# ============================================
#              LIST TASKS
# ============================================

def show_tasks(
    service,
    task_list,
    mode="all"
):

    task_list_id = task_list["id"]

    tasks = get_tasks(
        service,
        task_list_id,
        show_completed=True
    )

    today = datetime.now().date()

    filtered = []

    for task in tasks:

        status = task.get(
            "status"
        )

        if mode == "completed":

            if status == "completed":
                filtered.append(task)

            continue

        if mode == "all":

            if status != "completed":
                filtered.append(task)

            continue

        due = task.get("due")

        if not due:
            continue

        try:

            due_date = datetime.fromisoformat(
                due.replace(
                    "Z",
                    "+00:00"
                )
            ).astimezone().date()

        except Exception:

            continue

        if mode == "today":

            if due_date == today:
                filtered.append(task)

        elif mode == "week":

            if today <= due_date <= today + timedelta(days=7):
                filtered.append(task)

        elif mode == "overdue":

            if due_date < today and status != "completed":
                filtered.append(task)

    print()

    box_top()

    title = task_list.get(
        "title",
        "TASKS"
    )

    box_line(
        title.upper(),
        MAGENTA
    )

    box_middle()

    if not filtered:

        box_line(
            "No tasks found.",
            GRAY
        )

    else:

        for i, task in enumerate(
            filtered,
            1
        ):

            task_title = task.get(
                "title",
                "(No title)"
            )

            if task.get(
                "status"
            ) == "completed":

                marker = "✓"

            else:

                marker = "○"

            due = format_due(task)

            text = f"{i}. {marker} {task_title}"

            if due != "NO DEADLINE":
                text += f"  [{due}]"

            box_line(
                text,
                GREEN if marker == "✓" else WHITE
            )

    box_bottom()

    print()

    return filtered


# ============================================
#              CREATE TASK
# ============================================

def create_task(
    service,
    task_list
):

    print()

    box_top()
    box_line(
        "CREATE TASK",
        MAGENTA
    )
    box_middle()

    box_line(
        f"List: {task_list['title']}",
        CYAN
    )

    box_bottom()

    print()

    title = input(
        color(
            "Title > ",
            CYAN
        )
    ).strip()

    if not title:

        print(
            color(
                "Title cannot be empty.",
                RED
            )
        )

        return

    print()

    due_text = input(
        color(
            "Due date (Enter for none) > ",
            CYAN
        )
    ).strip()

    due_date = None

    if due_text:

        due_date = parse_date(
            due_text
        )

        if due_date is None:

            print(
                color(
                    "Invalid date. Task not created.",
                    RED
                )
            )

            return

    print()

    notes = input(
        color(
            "Details / notes (Enter for none) > ",
            CYAN
        )
    ).strip()

    task = {
        "title": title
    }

    if notes:
        task["notes"] = notes

    if due_date:

        # Google Tasks accepts RFC3339.
        # The API effectively treats this as a
        # date-level deadline.
        task["due"] = (
            datetime.combine(
                due_date,
                datetime.min.time()
            ).isoformat()
            + "Z"
        )

    print()

    print(
        color(
            "Creating task...",
            YELLOW
        )
    )

    try:

        created = service.tasks().insert(
            tasklist=task_list["id"],
            body=task
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to create task: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Task created",
            GREEN
        )
    )

    display_task(created)

    print()


# ============================================
#               SELECT TASK
# ============================================

def select_task(
    service,
    task_list,
    mode="all"
):

    tasks = show_tasks(
        service,
        task_list,
        mode
    )

    if not tasks:

        return None

    while True:

        choice = input(
            color(
                "Select task > ",
                CYAN
            )
        ).strip()

        try:

            index = int(choice)

            if 1 <= index <= len(tasks):

                return tasks[index - 1]

        except ValueError:
            pass

        print(
            color(
                "Invalid selection.",
                RED
            )
        )


# ============================================
#                 EDIT TASK
# ============================================

def edit_task(
    service,
    task_list
):

    task = select_task(
        service,
        task_list
    )

    if task is None:
        return

    print()

    print(
        color(
            "What would you like to change?",
            CYAN
        )
    )

    print()
    print("  1. Title")
    print("  2. Due date")
    print("  3. Details / notes")
    print("  4. Complete / uncomplete")
    print("  5. Move to another list")
    print("  6. Delete")
    print("  7. Cancel")

    print()

    choice = input(
        color(
            "Select > ",
            CYAN
        )
    ).strip()

    # ----------------------------------------
    # Title
    # ----------------------------------------

    if choice == "1":

        print()

        print(
            color(
                f"Current: {task.get('title', '')}",
                GRAY
            )
        )

        new_title = input(
            color(
                "New title > ",
                CYAN
            )
        ).strip()

        if not new_title:
            return

        task["title"] = new_title

    # ----------------------------------------
    # Due date
    # ----------------------------------------

    elif choice == "2":

        print()

        print(
            color(
                "Enter 'none' to remove the deadline.",
                GRAY
            )
        )

        due_text = input(
            color(
                "New due date > ",
                CYAN
            )
        ).strip()

        if due_text.lower() == "none":

            task.pop(
                "due",
                None
            )

        else:

            due_date = parse_date(
                due_text
            )

            if due_date is None:

                print(
                    color(
                        "Invalid date.",
                        RED
                    )
                )

                return

            task["due"] = (
                datetime.combine(
                    due_date,
                    datetime.min.time()
                ).isoformat()
                + "Z"
            )

    # ----------------------------------------
    # Notes
    # ----------------------------------------

    elif choice == "3":

        print()

        print(
            color(
                "Enter 'none' to remove details.",
                GRAY
            )
        )

        notes = input(
            color(
                "New details > ",
                CYAN
            )
        )

        if notes.strip().lower() == "none":

            task.pop(
                "notes",
                None
            )

        else:

            task["notes"] = notes

    # ----------------------------------------
    # Complete / uncomplete
    # ----------------------------------------

    elif choice == "4":

        if task.get(
            "status"
        ) == "completed":

            task["status"] = "needsAction"

            task.pop(
                "completed",
                None
            )

        else:

            task["status"] = "completed"

    # ----------------------------------------
    # Move
    # ----------------------------------------

    elif choice == "5":

        destination = select_task_list(
            service
        )

        if destination is None:
            return

        if destination["id"] == task_list["id"]:

            print(
                color(
                    "Task is already in this list.",
                    YELLOW
                )
            )

            return

        try:

            service.tasks().move(
                tasklist=task_list["id"],
                task=task["id"],
                destinationTasklist=destination["id"]
            ).execute()

            print()

            print(
                color(
                    f"✓ Moved to {destination['title']}",
                    GREEN
                )
            )

        except Exception as e:

            print(
                color(
                    f"Failed to move task: {e}",
                    RED
                )
            )

        return

    # ----------------------------------------
    # Delete
    # ----------------------------------------

    elif choice == "6":

        delete_task(
            service,
            task_list,
            task
        )

        return

    # ----------------------------------------
    # Cancel
    # ----------------------------------------

    elif choice == "7":

        return

    else:

        print(
            color(
                "Invalid choice.",
                RED
            )
        )

        return

    # ----------------------------------------
    # Update
    # ----------------------------------------

    print()

    print(
        color(
            "Updating task...",
            YELLOW
        )
    )

    try:

        updated = service.tasks().update(
            tasklist=task_list["id"],
            task=task["id"],
            body=task
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to update task: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Task updated",
            GREEN
        )
    )

    display_task(updated)

    print()


# ============================================
#                DELETE TASK
# ============================================

def delete_task(
    service,
    task_list,
    task=None
):

    if task is None:

        task = select_task(
            service,
            task_list
        )

        if task is None:
            return

    title = task.get(
        "title",
        "(No title)"
    )

    print()

    print(
        color(
            f'Delete "{title}"?',
            RED
        )
    )

    confirmation = input(
        color(
            "Type YES to confirm > ",
            CYAN
        )
    ).strip()

    if confirmation != "YES":

        print(
            color(
                "Deletion cancelled.",
                GRAY
            )
        )

        return

    try:

        service.tasks().delete(
            tasklist=task_list["id"],
            task=task["id"]
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to delete task: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Task deleted",
            GREEN
        )
    )

    print()


# ============================================
#             COMPLETE / UNCOMPLETE
# ============================================

def toggle_task(
    service,
    task_list
):

    task = select_task(
        service,
        task_list
    )

    if task is None:
        return

    if task.get(
        "status"
    ) == "completed":

        task["status"] = "needsAction"

        task.pop(
            "completed",
            None
        )

        message = "Task marked as incomplete."

    else:

        task["status"] = "completed"

        message = "Task completed."

    try:

        service.tasks().update(
            tasklist=task_list["id"],
            task=task["id"],
            body=task
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to update task: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            f"✓ {message}",
            GREEN
        )
    )

    print()


# ============================================
#             CLEAR COMPLETED
# ============================================

def clear_completed(
    service,
    task_list
):

    print()

    confirmation = input(
        color(
            f"Clear completed tasks from "
            f'"{task_list["title"]}"? (y/n) > ',
            CYAN
        )
    ).strip().lower()

    if confirmation not in (
        "y",
        "yes"
    ):

        print(
            color(
                "Cancelled.",
                GRAY
            )
        )

        return

    try:

        service.tasks().clear(
            tasklist=task_list["id"]
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to clear tasks: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Completed tasks cleared",
            GREEN
        )
    )

    print()


# ============================================
#               LIST MANAGEMENT
# ============================================

def create_task_list(service):

    print()

    title = input(
        color(
            "New task list name > ",
            CYAN
        )
    ).strip()

    if not title:
        return

    try:

        service.tasklists().insert(
            body={
                "title": title
            }
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to create list: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            f"✓ Created task list: {title}",
            GREEN
        )
    )

    print()


def rename_task_list(service):

    task_list = select_task_list(
        service
    )

    if task_list is None:
        return

    new_name = input(
        color(
            "New list name > ",
            CYAN
        )
    ).strip()

    if not new_name:
        return

    task_list["title"] = new_name

    try:

        service.tasklists().update(
            tasklist=task_list["id"],
            body=task_list
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to rename list: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Task list renamed",
            GREEN
        )
    )

    print()


def delete_task_list(service):

    task_list = select_task_list(
        service
    )

    if task_list is None:
        return

    print()

    confirmation = input(
        color(
            f'Delete list "{task_list["title"]}"? '
            f'This deletes its tasks too. (y/n) > ',
            RED
        )
    ).strip().lower()

    if confirmation not in (
        "y",
        "yes"
    ):

        print(
            color(
                "Cancelled.",
                GRAY
            )
        )

        return

    try:

        service.tasklists().delete(
            tasklist=task_list["id"]
        ).execute()

    except Exception as e:

        print(
            color(
                f"Failed to delete list: {e}",
                RED
            )
        )

        return

    print()

    print(
        color(
            "✓ Task list deleted",
            GREEN
        )
    )

    print()


# ============================================
#                   HELP
# ============================================

def tasks_help():

    print()

    box_top()
    box_line(
        "GOOGLE TASKS",
        MAGENTA
    )
    box_middle()

    commands = [
        ("tasks", "Open task list"),
        ("tasks my", "Open My Tasks"),
        ("tasks college", "Open College Work"),
        ("tasks add", "Create a task"),
        ("tasks edit", "Edit a task"),
        ("tasks delete", "Delete a task"),
        ("tasks done", "Complete / uncomplete"),
        ("tasks today", "Tasks due today"),
        ("tasks week", "Tasks due this week"),
        ("tasks overdue", "Overdue tasks"),
        ("tasks completed", "Completed tasks"),
        ("tasks clear", "Clear completed tasks"),
        ("tasks lists", "Show task lists"),
        ("tasks newlist", "Create a task list"),
        ("tasks renamelist", "Rename a task list"),
        ("tasks deletelist", "Delete a task list"),
    ]

    for command, description in commands:

        box_line(
            f"{command:<20} {description}",
            WHITE
        )

    box_bottom()

    print()


# ============================================
#                    MAIN
# ============================================

def main():

    args = sys.argv[1:]

    service = get_tasks_service()

    if service is None:
        return

    # ----------------------------------------
    # Help
    # ----------------------------------------

    if not args or args[0].lower() in (
        "help",
        "-h",
        "--help"
    ):

        tasks_help()
        return

    command = args[0].lower()

    # ----------------------------------------
    # List management
    # ----------------------------------------

    if command == "lists":

        lists = get_task_lists(
            service
        )

        print()

        for task_list in lists:

            print(
                color(
                    f"  • {task_list['title']}",
                    CYAN
                )
            )

        print()

        return

    if command == "newlist":

        create_task_list(
            service
        )

        return

    if command == "renamelist":

        rename_task_list(
            service
        )

        return

    if command == "deletelist":

        delete_task_list(
            service
        )

        return

    # ----------------------------------------
    # Select list
    # ----------------------------------------

    list_name = None

    if command in (
        "my",
        "college",
        "tasks"
    ):

        list_name = command

    task_list = resolve_list(
        service,
        list_name
    )

    if task_list is None:
        return

    # ----------------------------------------
    # Default: show tasks
    # ----------------------------------------

    if command in (
        "my",
        "college",
        "tasks"
    ):

        show_tasks(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Add
    # ----------------------------------------

    if command in (
        "add",
        "create"
    ):

        create_task(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Edit
    # ----------------------------------------

    if command in (
        "edit",
        "update"
    ):

        edit_task(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Delete
    # ----------------------------------------

    if command == "delete":

        delete_task(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Complete
    # ----------------------------------------

    if command in (
        "done",
        "complete"
    ):

        toggle_task(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Today
    # ----------------------------------------

    if command == "today":

        show_tasks(
            service,
            task_list,
            "today"
        )

        return

    # ----------------------------------------
    # Week
    # ----------------------------------------

    if command == "week":

        show_tasks(
            service,
            task_list,
            "week"
        )

        return

    # ----------------------------------------
    # Overdue
    # ----------------------------------------

    if command == "overdue":

        show_tasks(
            service,
            task_list,
            "overdue"
        )

        return

    # ----------------------------------------
    # Completed
    # ----------------------------------------

    if command == "completed":

        show_tasks(
            service,
            task_list,
            "completed"
        )

        return

    # ----------------------------------------
    # Clear
    # ----------------------------------------

    if command == "clear":

        clear_completed(
            service,
            task_list
        )

        return

    # ----------------------------------------
    # Unknown
    # ----------------------------------------

    print()

    print(
        color(
            f"Unknown tasks command: {command}",
            RED
        )
    )

    print(
        "Use 'tasks help' for available commands."
    )

    print()


if __name__ == "__main__":
    main()

# ============================================
#          POWERSHELL ENTRY POINT
# ============================================

def tasks(*args):

    old_argv = sys.argv

    try:

        sys.argv = [
            "tasks"
        ] + list(args)

        main()

    finally:

        sys.argv = old_argv