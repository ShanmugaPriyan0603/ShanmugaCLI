from planner.models import ScheduleBlock
from planner.validator import validate_blocks


def test_overlap_is_reported():
    blocks = [
        ScheduleBlock(date="2026-10-26", start="09:00", end="10:00", title="A"),
        ScheduleBlock(date="2026-10-26", start="09:30", end="10:30", title="B"),
    ]
    assert any(issue.code == "overlap" for issue in validate_blocks(blocks))


def test_invalid_time_is_reported():
    block = ScheduleBlock(date="2026-10-26", start="10:00", end="09:00", title="A")
    assert any(issue.code == "invalid_time" for issue in validate_blocks([block]))
