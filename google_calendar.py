from pathlib import Path
from datetime import datetime, timedelta, date, timezone
import uuid
import sys
import calendar as pycalendar

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# ============================================
#              CONFIGURATION
# ============================================

BASE_DIR = Path.home() / "ShanmugaCLI" / "google"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


# ============================================
#                  COLORS
# ============================================

RESET = "\033[0m"

PINK = "\033[38;2;242;167;216m"
CYAN = "\033[38;2;139;233;253m"
YELLOW = "\033[38;2;246;211;101m"
GREEN = "\033[38;2;159;226;191m"
PURPLE = "\033[38;2;200;162;255m"
GRAY = "\033[38;2;110;110;130m"
WHITE = "\033[38;2;235;235;245m"


def color(text, colour):
    return f"{colour}{text}{RESET}"


# ============================================
#             GOOGLE CALENDAR
# ============================================

def get_calendar_service():

    if not TOKEN_FILE.exists():
        print()
        print("Google authentication token not found.")
        print()
        print(r'Run: python "$HOME\ShanmugaCLI\google_auth.py"')
        print()
        return None

    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


# ============================================
#                 DATE HELPERS
# ============================================

def start_of_day(d):

    return datetime(
        d.year,
        d.month,
        d.day
    )


def parse_date(text):

    text = text.strip().lower()

    today = date.today()

    if text == "today":
        return today

    if text == "tomorrow":
        return today + timedelta(days=1)

    if text == "yesterday":
        return today - timedelta(days=1)

    # -----------------------------
    # Full dates
    # -----------------------------

    for fmt in [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y"
    ]:

        try:

            return datetime.strptime(
                text,
                fmt
            ).date()

        except ValueError:
            pass

    # -----------------------------
    # Month + day, current year
    # -----------------------------

    for fmt in [
        "%B %d",
        "%b %d",
        "%d %B",
        "%d %b"
    ]:

        try:

            parsed = datetime.strptime(
                f"{text};{today.year}",
                f"{fmt};%Y"
            ).date()

            return parsed

        except ValueError:
            pass

    # -----------------------------
    # Weekdays
    # -----------------------------

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    if text in weekdays:

        target = weekdays[text]
        current = today.weekday()

        days_ahead = (
            target - current
        ) % 7

        return today + timedelta(
            days=days_ahead
        )

    # -----------------------------
    # Next weekday
    # -----------------------------

    if text.startswith("next "):

        weekday = text[5:].strip()

        if weekday in weekdays:

            target = weekdays[weekday]
            current = today.weekday()

            days_ahead = (
                target - current
            ) % 7

            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(
                days=days_ahead
            )

    return None


# ============================================
#              GET EVENTS
# ============================================

def get_events(
    service,
    start,
    end
):

    result = service.events().list(
        calendarId="primary",

        timeMin=start.astimezone().isoformat(),
        timeMax=end.astimezone().isoformat(),

        singleEvents=True,

        orderBy="startTime"
    ).execute()

    return result.get(
        "items",
        []
    )


# ============================================
#              EVENT HELPERS
# ============================================

def get_event_datetime(event):

    start = event.get(
        "start",
        {}
    )

    if "dateTime" in start:

        return datetime.fromisoformat(
            start["dateTime"].replace(
                "Z",
                "+00:00"
            )
        )

    return None


def get_event_date(event):

    start = event.get(
        "start",
        {}
    )

    if "date" in start:

        return datetime.strptime(
            start["date"],
            "%Y-%m-%d"
        ).date()

    dt = get_event_datetime(event)

    if dt:

        return dt.astimezone().date()

    return None


def format_time(event):

    dt = get_event_datetime(event)

    if dt is None:
        return "ALL DAY"

    return dt.astimezone().strftime(
        "%H:%M"
    )


# ============================================
#               DRAW EVENT BOX
# ============================================

def draw_box(
    title,
    events,
    show_dates=False
):

    width = 48

    print()

    # Top border
    print(
        color(
            "╭" + "─" * width + "╮",
            GRAY
        )
    )

    # Title
    padding = width - len(title)

    left = padding // 2
    right = padding - left

    print(
        color("│", GRAY)
        + color(
            " " * left
            + title
            + " " * right,
            PINK
        )
        + color("│", GRAY)
    )

    # Separator
    print(
        color(
            "├" + "─" * width + "┤",
            GRAY
        )
    )

    # No events
    if not events:

        text = "No events scheduled."

        padding = width - len(text)

        left = padding // 2
        right = padding - left

        print(
            color("│", GRAY)
            + color(
                " " * left
                + text
                + " " * right,
                PURPLE
            )
            + color("│", GRAY)
        )

    else:

        last_date = None

        for event in events:

            event_date = get_event_date(
                event
            )

            # Date headings for week view
            if show_dates and event_date != last_date:

                if last_date is not None:

                    print(
                        color(
                            "│"
                            + " " * width
                            + "│",
                            GRAY
                        )
                    )

                date_text = event_date.strftime(
                    "%a · %b %d"
                )

                line = (
                    f"  {date_text}"
                ).ljust(width)

                print(
                    color("│", GRAY)
                    + color(
                        line,
                        CYAN
                    )
                    + color("│", GRAY)
                )

                last_date = event_date

            time = format_time(
                event
            )

            summary = event.get(
                "summary",
                "(No title)"
            )

            prefix = f"  {time} ── "

            available = (
                width
                - len(prefix)
            )

            if len(summary) > available:

                summary = (
                    summary[:available - 3]
                    + "..."
                )

            remaining = (
                width
                - len(prefix)
                - len(summary)
            )

            print(
                color("│", GRAY)
                + color(
                    prefix,
                    YELLOW
                )
                + color(
                    summary,
                    WHITE
                )
                + " " * remaining
                + color("│", GRAY)
            )

    # Bottom border
    print(
        color(
            "╰" + "─" * width + "╯",
            GRAY
        )
    )

    print()


# ============================================
#               SHOW SINGLE DAY
# ============================================

def show_single_day(
    service,
    target
):

    start = start_of_day(
        target
    )

    end = start + timedelta(
        days=1
    )

    events = get_events(
        service,
        start,
        end
    )

    title = target.strftime(
        "%A · %B %d, %Y"
    ).upper()

    draw_box(
        title,
        events
    )


# ============================================
#                 SHOW WEEK
# ============================================

def show_week(service):

    today = date.today()

    start = start_of_day(
        today
    )

    end = start + timedelta(
        days=7
    )

    events = get_events(
        service,
        start,
        end
    )

    draw_box(
        "NEXT 7 DAYS",
        events,
        show_dates=True
    )


# ============================================
#                MONTH HELPERS
# ============================================

def parse_month(args):

    today = date.today()

    if not args:

        return today.year, today.month

    text = " ".join(
        args
    ).strip().lower()

    # -----------------------------
    # Next month
    # -----------------------------

    if text == "next":

        if today.month == 12:

            return today.year + 1, 1

        return today.year, today.month + 1

    # -----------------------------
    # Previous month
    # -----------------------------

    if text in [
        "previous",
        "prev"
    ]:

        if today.month == 1:

            return today.year - 1, 12

        return today.year, today.month - 1

    # -----------------------------
    # Numeric month
    # -----------------------------

    try:

        month_number = int(text)

        if 1 <= month_number <= 12:

            return (
                today.year,
                month_number
            )

    except ValueError:
        pass

    # -----------------------------
    # Month name
    # -----------------------------

    for fmt in [
        "%B",
        "%b"
    ]:

        try:

            parsed = datetime.strptime(
                text,
                fmt
            )

            return (
                today.year,
                parsed.month
            )

        except ValueError:
            pass

    # -----------------------------
    # Month + year
    # -----------------------------

    for fmt in [
        "%B %Y",
        "%b %Y"
    ]:

        try:

            parsed = datetime.strptime(
                text,
                fmt
            )

            return (
                parsed.year,
                parsed.month
            )

        except ValueError:
            pass

    return None


# ============================================
#              DRAW MONTH GRID
# ============================================

def show_month(
    service,
    year,
    month
):

    first_day = date(
        year,
        month,
        1
    )

    # Find first day of next month
    if month == 12:

        next_month = date(
            year + 1,
            1,
            1
        )

    else:

        next_month = date(
            year,
            month + 1,
            1
        )

    # Get all events in this month
    events = get_events(
        service,
        start_of_day(first_day),
        start_of_day(next_month)
    )

    # ----------------------------------------
    # Map events to dates
    # ----------------------------------------

    event_days = {}

    for event in events:

        event_date = get_event_date(
            event
        )

        if event_date is None:
            continue

        if event_date not in event_days:

            event_days[event_date] = []

        event_days[event_date].append(
            event
        )

    # ----------------------------------------
    # Calendar setup
    # ----------------------------------------

    cal = pycalendar.Calendar(
        firstweekday=0
    )

    weeks = cal.monthdayscalendar(
        year,
        month
    )

    cell_width = 8

    # 7 × 8 = 56 visible characters
    width = cell_width * 7

    title = datetime(
        year,
        month,
        1
    ).strftime(
        "%B %Y"
    ).upper()

    print()

    # ----------------------------------------
    # Top border
    # ----------------------------------------

    print(
        color(
            "╭" + "─" * width + "╮",
            GRAY
        )
    )

    # ----------------------------------------
    # Month title
    # ----------------------------------------

    padding = width - len(title)

    left = padding // 2
    right = padding - left

    print(
        color("│", GRAY)
        + color(
            " " * left
            + title
            + " " * right,
            PINK
        )
        + color("│", GRAY)
    )

    # ----------------------------------------
    # Separator
    # ----------------------------------------

    print(
        color(
            "├" + "─" * width + "┤",
            GRAY
        )
    )

    # ----------------------------------------
    # Weekday header
    # ----------------------------------------

    weekdays = [
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
        "SAT",
        "SUN"
    ]

    header = ""

    for day in weekdays:

        header += color(
            day.center(cell_width),
            CYAN
        )

    print(
        color("│", GRAY)
        + header
        + color("│", GRAY)
    )

    # ----------------------------------------
    # Separator
    # ----------------------------------------

    print(
        color(
            "├" + "─" * width + "┤",
            GRAY
        )
    )

    today = date.today()

    # ----------------------------------------
    # Calendar rows
    # ----------------------------------------

    for week in weeks:

        row = ""

        for day in week:

            # Empty cell
            if day == 0:

                row += (
                    " " * cell_width
                )

                continue

            current = date(
                year,
                month,
                day
            )

            has_events = (
                current in event_days
            )

            marker = ""

            if has_events:
                marker = "•"

            # --------------------------------
            # Today
            # --------------------------------

            if current == today:

                text = (
                    f"[{day:2}{marker}]"
                )

                row += color(
                    text.center(
                        cell_width
                    ),
                    PURPLE
                )

            # --------------------------------
            # Event day
            # --------------------------------

            elif has_events:

                text = (
                    f"{day:2}{marker}"
                )

                row += color(
                    text.center(
                        cell_width
                    ),
                    GREEN
                )

            # --------------------------------
            # Normal day
            # --------------------------------

            else:

                text = f"{day:2}"

                row += color(
                    text.center(
                        cell_width
                    ),
                    WHITE
                )

        print(
            color("│", GRAY)
            + row
            + color("│", GRAY)
        )

    # ----------------------------------------
    # Event separator
    # ----------------------------------------

    print(
        color(
            "├" + "─" * width + "┤",
            GRAY
        )
    )

    # ----------------------------------------
    # Event summary
    # ----------------------------------------

    if events:

        sorted_events = sorted(
            events,
            key=lambda e: (
                get_event_date(e),
                get_event_datetime(e).timestamp()
		if get_event_datetime(e)
        	else float("-inf")
            )
        )

        for event in sorted_events:

            event_date = get_event_date(
                event
            )

            time = format_time(
                event
            )

            summary = event.get(
                "summary",
                "(No title)"
            )

            date_text = (
                f"{event_date.day:2}"
            )

            prefix = (
                f"  {date_text} · "
                f"{time} ── "
            )

            available = (
                width
                - len(prefix)
            )

            if len(summary) > available:

                summary = (
                    summary[:available - 3]
                    + "..."
                )

            remaining = (
                width
                - len(prefix)
                - len(summary)
            )

            print(
                color("│", GRAY)
                + color(
                    prefix,
                    YELLOW
                )
                + color(
                    summary,
                    WHITE
                )
                + " " * remaining
                + color("│", GRAY)
            )

    else:

        text = "No events this month."

        print(
            color("│", GRAY)
            + color(
                text.center(width),
                PURPLE
            )
            + color("│", GRAY)
        )

    # ----------------------------------------
    # Bottom border
    # ----------------------------------------

    print(
        color(
            "╰" + "─" * width + "╯",
            GRAY
        )
    )

    print()


# ============================================
#                    MAIN
# ============================================
# ============================================
#               CREATE EVENT
# ============================================

def create_event(service, target):

    print()

    print(
        color(
            "╭" + "─" * 56 + "╮",
            GRAY
        )
    )

    title = "CREATE EVENT"

    padding = 56 - len(title)
    left = padding // 2
    right = padding - left

    print(
        color("│", GRAY)
        + color(
            " " * left
            + title
            + " " * right,
            PINK
        )
        + color("│", GRAY)
    )

    print(
        color(
            "├" + "─" * 56 + "┤",
            GRAY
        )
    )

    date_text = target.strftime(
        "%A · %B %d, %Y"
    ).upper()

    print(
        color("│", GRAY)
        + color(
            f"  Date       {date_text}".ljust(56),
            CYAN
        )
        + color("│", GRAY)
    )

    print(
        color(
            "│" + " " * 56 + "│",
            GRAY
        )
    )

    print(
        color(
            "╰" + "─" * 56 + "╯",
            GRAY
        )
    )

    print()

    # ----------------------------------------
    # Title
    # ----------------------------------------

    while True:

        event_title = input(
            color(
                "  Title      > ",
                CYAN
            )
        ).strip()

        if event_title:
            break

        print(
            color(
                "  Title cannot be empty.",
                PINK
            )
        )

    print()

    # ----------------------------------------
    # All day / timed
    # ----------------------------------------

    print(
        color(
            "  When:",
            CYAN
        )
    )

    print(
        "    "
        + color("1.", YELLOW)
        + " All day"
    )

    print(
        "    "
        + color("2.", YELLOW)
        + " Specific time"
    )

    while True:

        choice = input(
            color(
                "\n  > ",
                CYAN
            )
        ).strip()

        if choice in ("1", "2"):
            break

        print(
            color(
                "  Please enter 1 or 2.",
                PINK
            )
        )

    # ----------------------------------------
    # Build event
    # ----------------------------------------

    event = {
        "summary": event_title
    }

    if choice == "1":

        # Google Calendar all-day events use
        # date-only values.
        event["start"] = {
            "date": target.isoformat()
        }

        # End date is exclusive.
        event["end"] = {
            "date": (
                target + timedelta(days=1)
            ).isoformat()
        }

    else:

        # ------------------------------------
        # Start time
        # ------------------------------------

        while True:

            start_text = input(
                color(
                    "\n  Start time > ",
                    CYAN
                )
            ).strip()

            try:

                start_time = datetime.strptime(
                    start_text,
                    "%H:%M"
                ).time()

                break

            except ValueError:

                print(
                    color(
                        "  Use 24-hour format, e.g. 14:30",
                        PINK
                    )
                )

        # ------------------------------------
        # End time
        # ------------------------------------

        while True:

            end_text = input(
                color(
                    "  End time   > ",
                    CYAN
                )
            ).strip()

            try:

                end_time = datetime.strptime(
                    end_text,
                    "%H:%M"
                ).time()

                break

            except ValueError:

                print(
                    color(
                        "  Use 24-hour format, e.g. 16:00",
                        PINK
                    )
                )

        start_dt = datetime.combine(
            target,
            start_time
        )

        end_dt = datetime.combine(
            target,
            end_time
        )

        if end_dt <= start_dt:

            print()

            print(
                color(
                    "  End time must be after start time.",
                    PINK
                )
            )

            return

        # ------------------------------------
        # Local timezone
        # ------------------------------------

        local_tz = datetime.now().astimezone().tzinfo

        start_dt = start_dt.replace(
            tzinfo=local_tz
        )

        end_dt = end_dt.replace(
            tzinfo=local_tz
        )

        event["start"] = {
            "dateTime": start_dt.isoformat()
        }

        event["end"] = {
            "dateTime": end_dt.isoformat()
        }

    print()

    # ----------------------------------------
    # Google Meet
    # ----------------------------------------

    while True:

        meet = input(
            color(
                "  Google Meet? (y/n) > ",
                CYAN
            )
        ).strip().lower()

        if meet in ("y", "yes", "n", "no"):
            break

        print(
            color(
                "  Please enter y or n.",
                PINK
            )
        )

    # ----------------------------------------
    # Create Meet request
    # ----------------------------------------

    if meet in ("y", "yes"):

        event["conferenceData"] = {
            "createRequest": {
                "requestId": str(
                    uuid.uuid4()
                ),
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                }
            }
        }

    # ----------------------------------------
    # Confirmation
    # ----------------------------------------

    print()

    print(
        color(
            "  Creating event...",
            YELLOW
        )
    )

    try:

        created = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()

    except Exception as e:

        print()

        print(
            color(
                "  ✗ Failed to create event.",
                PINK
            )
        )

        print(
            color(
                f"    {e}",
                GRAY
            )
        )

        print()

        return

    # ----------------------------------------
    # Success
    # ----------------------------------------

    print()

    print(
        color(
            "  ✓ Event created",
            GREEN
        )
    )

    if meet in ("y", "yes"):

        conference = created.get(
            "conferenceData",
            {}
        )

        entry_points = conference.get(
            "entryPoints",
            []
        )

        meet_url = None

        for entry in entry_points:

            if entry.get("entryPointType") == "video":

                meet_url = entry.get(
                    "uri"
                )

                break

        if meet_url:

            print(
                color(
                    "  ✓ Google Meet created",
                    GREEN
                )
            )

            print(
                color(
                    f"    {meet_url}",
                    CYAN
                )
            )

        else:

            print(
                color(
                    "  ✓ Google Meet requested",
                    GREEN
                )
            )

            print(
                color(
                    "    Google is still generating the meeting link.",
                    GRAY
                )
            )

    print()

    html_link = created.get(
        "htmlLink"
    )

    if html_link:

        print(
            color(
                f"  Calendar: {html_link}",
                GRAY
            )
        )

    print()
# ============================================
#               SELECT EVENT
# ============================================

def select_event(service, target, action):

    start = start_of_day(target)
    end = start + timedelta(days=1)

    events = get_events(
        service,
        start,
        end
    )

    if not events:

        print()

        print(
            color(
                f"No events found for {target.strftime('%A, %B %d, %Y')}.",
                PINK
            )
        )

        print()

        return None

    print()

    print(
        color(
            "╭" + "─" * 56 + "╮",
            GRAY
        )
    )

    title = action.upper() + " EVENT"

    padding = 56 - len(title)
    left = padding // 2
    right = padding - left

    print(
        color("│", GRAY)
        + color(
            " " * left
            + title
            + " " * right,
            PINK
        )
        + color("│", GRAY)
    )

    print(
        color(
            "├" + "─" * 56 + "┤",
            GRAY
        )
    )

    for i, event in enumerate(events, 1):

        summary = event.get(
            "summary",
            "(No title)"
        )

        time = format_time(event)

        line = f"  {i}. {summary}"

        if len(line) > 56:
            line = line[:53] + "..."

        print(
            color("│", GRAY)
            + color(
                line.ljust(56),
                WHITE
            )
            + color("│", GRAY)
        )

        detail = f"     {time}"

        print(
            color("│", GRAY)
            + color(
                detail.ljust(56),
                YELLOW
            )
            + color("│", GRAY)
        )

        if i != len(events):

            print(
                color(
                    "│" + " " * 56 + "│",
                    GRAY
                )
            )

    print(
        color(
            "╰" + "─" * 56 + "╯",
            GRAY
        )
    )

    print()

    while True:

        choice = input(
            color(
                "Select event > ",
                CYAN
            )
        ).strip()

        try:

            index = int(choice)

            if 1 <= index <= len(events):

                return events[index - 1]

        except ValueError:
            pass

        print(
            color(
                f"Please enter a number from 1 to {len(events)}.",
                PINK
            )
        )


# ============================================
#                EDIT EVENT
# ============================================

def edit_event(service, target):

    event = select_event(
        service,
        target,
        "EDIT"
    )

    if event is None:
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
    print("  2. Date")
    print("  3. Time")
    print("  4. Google Meet")
    print("  5. Cancel")

    print()

    while True:

        choice = input(
            color(
                "Select > ",
                CYAN
            )
        ).strip()

        if choice in ("1", "2", "3", "4", "5"):
            break

        print(
            color(
                "Please enter a number from 1 to 5.",
                PINK
            )
        )

    # ----------------------------------------
    # Title
    # ----------------------------------------

    if choice == "1":

        current = event.get(
            "summary",
            ""
        )

        print()

        print(
            color(
                f"Current title: {current}",
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

            print(
                color(
                    "Title cannot be empty.",
                    PINK
                )
            )

            return

        event["summary"] = new_title

    # ----------------------------------------
    # Date
    # ----------------------------------------

    elif choice == "2":

        print()

        new_date_text = input(
            color(
                "New date > ",
                CYAN
            )
        ).strip()

        new_date = parse_date(
            new_date_text
        )

        if new_date is None:

            print(
                color(
                    "I couldn't understand that date.",
                    PINK
                )
            )

            return

        start = event.get(
            "start",
            {}
        )

        end = event.get(
            "end",
            {}
        )

        # All-day event
        if "date" in start:

            old_start = datetime.strptime(
                start["date"],
                "%Y-%m-%d"
            ).date()

            old_end = datetime.strptime(
                end["date"],
                "%Y-%m-%d"
            ).date()

            duration = (
                old_end - old_start
            ).days

            event["start"]["date"] = (
                new_date.isoformat()
            )

            event["end"]["date"] = (
                new_date
                + timedelta(days=duration)
            ).isoformat()

        # Timed event
        else:

            start_dt = get_event_datetime(
                event
            )

            if start_dt is None:

                print(
                    color(
                        "Could not determine event time.",
                        PINK
                    )
                )

                return

            old_start_date = (
                start_dt.astimezone().date()
            )

            delta = (
                new_date
                - old_start_date
            )

            old_start = start_dt + delta

            end_dt = datetime.fromisoformat(
                end["dateTime"].replace(
                    "Z",
                    "+00:00"
                )
            )

            old_end = end_dt + delta

            event["start"]["dateTime"] = (
                old_start.isoformat()
            )

            event["end"]["dateTime"] = (
                old_end.isoformat()
            )

    # ----------------------------------------
    # Time
    # ----------------------------------------

    elif choice == "3":

        start = event.get(
            "start",
            {}
        )

        # All-day → timed
        if "date" in start:

            event_date = datetime.strptime(
                start["date"],
                "%Y-%m-%d"
            ).date()

            print()

            start_text = input(
                color(
                    "Start time > ",
                    CYAN
                )
            ).strip()

            end_text = input(
                color(
                    "End time   > ",
                    CYAN
                )
            ).strip()

            try:

                start_time = datetime.strptime(
                    start_text,
                    "%H:%M"
                ).time()

                end_time = datetime.strptime(
                    end_text,
                    "%H:%M"
                ).time()

            except ValueError:

                print(
                    color(
                        "Use 24-hour format, e.g. 14:30.",
                        PINK
                    )
                )

                return

            start_dt = datetime.combine(
                event_date,
                start_time
            )

            end_dt = datetime.combine(
                event_date,
                end_time
            )

            if end_dt <= start_dt:

                print(
                    color(
                        "End time must be after start time.",
                        PINK
                    )
                )

                return

            tz = datetime.now().astimezone().tzinfo

            start_dt = start_dt.replace(
                tzinfo=tz
            )

            end_dt = end_dt.replace(
                tzinfo=tz
            )

            # Remove all-day fields
            event["start"].pop(
                "date",
                None
            )

            event["end"].pop(
                "date",
                None
            )

            event["start"]["dateTime"] = (
                start_dt.isoformat()
            )

            event["end"]["dateTime"] = (
                end_dt.isoformat()
            )

        else:

            start_dt = get_event_datetime(
                event
            )

            end_dt = datetime.fromisoformat(
                event["end"]["dateTime"].replace(
                    "Z",
                    "+00:00"
                )
            )

            print()

            start_text = input(
                color(
                    "New start time > ",
                    CYAN
                )
            ).strip()

            end_text = input(
                color(
                    "New end time   > ",
                    CYAN
                )
            ).strip()

            try:

                start_time = datetime.strptime(
                    start_text,
                    "%H:%M"
                ).time()

                end_time = datetime.strptime(
                    end_text,
                    "%H:%M"
                ).time()

            except ValueError:

                print(
                    color(
                        "Use 24-hour format, e.g. 14:30.",
                        PINK
                    )
                )

                return

            start_date = (
                start_dt.astimezone().date()
            )

            new_start = datetime.combine(
                start_date,
                start_time
            )

            new_end = datetime.combine(
                start_date,
                end_time
            )

            if new_end <= new_start:

                print(
                    color(
                        "End time must be after start time.",
                        PINK
                    )
                )

                return

            tz = datetime.now().astimezone().tzinfo

            new_start = new_start.replace(
                tzinfo=tz
            )

            new_end = new_end.replace(
                tzinfo=tz
            )

            event["start"]["dateTime"] = (
                new_start.isoformat()
            )

            event["end"]["dateTime"] = (
                new_end.isoformat()
            )

    # ----------------------------------------
    # Google Meet
    # ----------------------------------------

    elif choice == "4":

        conference = event.get(
            "conferenceData"
        )

        currently_has_meet = bool(
            conference
        )

        print()

        if currently_has_meet:

            print(
                color(
                    "This event already has a Google Meet.",
                    GREEN
                )
            )

            print()

            remove = input(
                color(
                    "Remove Google Meet? (y/n) > ",
                    CYAN
                )
            ).strip().lower()

            if remove in ("y", "yes"):

                event.pop(
                    "conferenceData",
                    None
                )

        else:

            add = input(
                color(
                    "Add Google Meet? (y/n) > ",
                    CYAN
                )
            ).strip().lower()

            if add in ("y", "yes"):

                event["conferenceData"] = {
                    "createRequest": {
                        "requestId": str(
                            uuid.uuid4()
                        ),
                        "conferenceSolutionKey": {
                            "type": "hangoutsMeet"
                        }
                    }
                }

    # ----------------------------------------
    # Cancel
    # ----------------------------------------

    elif choice == "5":

        print()

        print(
            color(
                "Edit cancelled.",
                GRAY
            )
        )

        return

    # ----------------------------------------
    # Update Google Calendar
    # ----------------------------------------

    print()

    print(
        color(
            "Updating event...",
            YELLOW
        )
    )

    try:

        updated = service.events().update(
            calendarId="primary",
            eventId=event["id"],
            body=event,
            conferenceDataVersion=1
        ).execute()

    except Exception as e:

        print()

        print(
            color(
                "✗ Failed to update event.",
                PINK
            )
        )

        print(
            color(
                f"  {e}",
                GRAY
            )
        )

        print()

        return

    print()

    print(
        color(
            "✓ Event updated",
            GREEN
        )
    )

    # Show new Meet link if one exists
    conference = updated.get(
        "conferenceData",
        {}
    )

    if conference:

        for entry in conference.get(
            "entryPoints",
            []
        ):

            if entry.get(
                "entryPointType"
            ) == "video":

                print(
                    color(
                        f"  Meet: {entry.get('uri')}",
                        CYAN
                    )
                )

                break

    print()


# ============================================
#               DELETE EVENT
# ============================================

def delete_event(service, target):

    event = select_event(
        service,
        target,
        "DELETE"
    )

    if event is None:
        return

    summary = event.get(
        "summary",
        "(No title)"
    )

    print()

    print(
        color(
            f'Delete "{summary}"?',
            PINK
        )
    )

    print()

    confirmation = input(
        color(
            "Type YES to confirm > ",
            CYAN
        )
    ).strip()

    if confirmation != "YES":

        print()

        print(
            color(
                "Deletion cancelled.",
                GRAY
            )
        )

        print()

        return

    print()

    print(
        color(
            "Deleting event...",
            YELLOW
        )
    )

    try:

        service.events().delete(
            calendarId="primary",
            eventId=event["id"]
        ).execute()

    except Exception as e:

        print()

        print(
            color(
                "✗ Failed to delete event.",
                PINK
            )
        )

        print(
            color(
                f"  {e}",
                GRAY
            )
        )

        print()

        return

    print()

    print(
        color(
            "✓ Event deleted",
            GREEN
        )
    )

    print()

def main():

    args = sys.argv[1:]
        # ----------------------------------------
    # Create event
    # ----------------------------------------

    if args and args[0].lower() == "create":

        if len(args) < 2:

            print()

            print(
                color(
                    "Usage:",
                    CYAN
                )
            )

            print(
                "  cal create monday"
            )

            print(
                '  cal create "15 September"'
            )

            print()

            return

        target = parse_date(
            " ".join(args[1:])
        )

        if target is None:

            print()

            print(
                color(
                    "I couldn't understand that date.",
                    PINK
                )
            )

            print()

            return

        service = get_calendar_service()

        if service:

            create_event(
                service,
                target
            )

        return


    # ----------------------------------------
    # Edit event
    # ----------------------------------------

    if args and args[0].lower() == "edit":

        if len(args) < 2:

            print()

            print(
                color(
                    "Usage:",
                    CYAN
                )
            )

            print(
                "  cal edit monday"
            )

            print(
                '  cal edit "15 September"'
            )

            print()

            return

        target = parse_date(
            " ".join(args[1:])
        )

        if target is None:

            print()

            print(
                color(
                    "I couldn't understand that date.",
                    PINK
                )
            )

            print()

            return

        service = get_calendar_service()

        if service:

            edit_event(
                service,
                target
            )

        return


    # ----------------------------------------
    # Delete event
    # ----------------------------------------

    if args and args[0].lower() == "delete":

        if len(args) < 2:

            print()

            print(
                color(
                    "Usage:",
                    CYAN
                )
            )

            print(
                "  cal delete monday"
            )

            print(
                '  cal delete "15 September"'
            )

            print()

            return

        target = parse_date(
            " ".join(args[1:])
        )

        if target is None:

            print()

            print(
                color(
                    "I couldn't understand that date.",
                    PINK
                )
            )

            print()

            return

        service = get_calendar_service()

        if service:

            delete_event(
                service,
                target
            )

        return
        # ----------------------------------------
    # Create event
    # ----------------------------------------

    if args and args[0].lower() == "create":

        if len(args) < 2:

            print()

            print(
                color(
                    "Usage:",
                    CYAN
                )
            )

            print(
                "  cal create monday"
            )

            print(
                '  cal create "15 September"'
            )

            print(
                "  cal create 2026-09-15"
            )

            print()

            return

        create_args = args[1:]

        target = parse_date(
            " ".join(create_args)
        )

        if target is None:

            print()

            print(
                color(
                    "I couldn't understand that date.",
                    PINK
                )
            )

            print()

            return

        service = get_calendar_service()

        if service:

            create_event(
                service,
                target
            )

        return
    # ----------------------------------------
    # Default → Today
    # ----------------------------------------

    if not args:

        service = get_calendar_service()

        if service:

            show_single_day(
                service,
                date.today()
            )

        return

    # ----------------------------------------
    # Month
    # ----------------------------------------

    if args[0].lower() == "month":

        month_args = args[1:]

        parsed = parse_month(
            month_args
        )

        if parsed is None:

            print()
            print(
                color(
                    "I couldn't understand that month.",
                    PINK
                )
            )

            print()

            print(
                color(
                    "Examples:",
                    CYAN
                )
            )

            print(
                "  cal month"
            )

            print(
                "  cal month September"
            )

            print(
                "  cal month September 2027"
            )

            print(
                "  cal month next"
            )

            print(
                "  cal month previous"
            )

            print()

            return

        year, month = parsed

        service = get_calendar_service()

        if service:

            show_month(
                service,
                year,
                month
            )

        return

    # ----------------------------------------
    # Week
    # ----------------------------------------

    if args[0].lower() == "week":

        service = get_calendar_service()

        if service:

            show_week(
                service
            )

        return

    # ----------------------------------------
    # Normal date
    # ----------------------------------------

    mode = " ".join(
        args
    ).strip().lower()

    target = parse_date(
        mode
    )

    if target is None:

        print()

        print(
            color(
                "I couldn't understand that date.",
                PINK
            )
        )

        print()

        print(
            color(
                "Examples:",
                CYAN
            )
        )

        print(
            "  cal today"
        )

        print(
            "  cal tomorrow"
        )

        print(
            "  cal monday"
        )

        print(
            "  cal next monday"
        )

        print(
            '  cal "6 March"'
        )

        print(
            '  cal "15 September"'
        )

        print(
            "  cal 2026-09-15"
        )

        print(
            "  cal 15/09/2026"
        )

        print(
            "  cal week"
        )

        print(
            "  cal month"
        )

        print()

        return

    service = get_calendar_service()

    if service:

        show_single_day(
            service,
            target
        )


# ============================================
#                    START
# ============================================

if __name__ == "__main__":
    main()