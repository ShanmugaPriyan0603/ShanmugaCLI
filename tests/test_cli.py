from planner.cli import day_help, study_help


def test_help_commands_are_available():
    assert "study subjects" in study_help()
    assert "day plan" in day_help()
