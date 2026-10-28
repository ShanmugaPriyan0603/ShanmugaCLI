from __future__ import annotations

from datetime import date, datetime, time, timedelta


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_time(value: str) -> time:
    return time.fromisoformat(value)


def minutes_between(start: str, end: str) -> int:
    start_time, end_time = parse_time(start), parse_time(end)
    delta = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)
    if delta.total_seconds() <= 0:
        delta += timedelta(days=1)
    return int(delta.total_seconds() // 60)


def add_minutes(start: str, minutes: int) -> str:
    result = datetime.combine(date.today(), parse_time(start)) + timedelta(minutes=minutes)
    return result.strftime("%H:%M")


def overlaps(first_start: str, first_end: str, second_start: str, second_end: str) -> bool:
    a, b = parse_time(first_start), parse_time(first_end)
    c, d = parse_time(second_start), parse_time(second_end)
    return a < d and c < b
