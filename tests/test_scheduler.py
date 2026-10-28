from datetime import date

from planner.models import Preferences
from planner.scheduler import schedule_tasks


def test_scheduler_allocates_and_reports_overflow():
    blocks, unscheduled = schedule_tasks(
        date(2026, 10, 26),
        [{"id": "a", "description": "A", "estimated_minutes": 60, "priority": 5},
         {"id": "b", "description": "B", "estimated_minutes": 60, "priority": 1}],
        Preferences(wake_time="09:00", sleep_time="10:00", break_minutes=0),
        [],
    )
    assert len(blocks) == 1
    assert len(unscheduled) == 1
