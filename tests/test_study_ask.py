import json

from planner.gemini_client import GeminiPlanner
from planner.storage import JsonStore
from planner.study_engine import normalize_study_intake, save_study_intake


class FakeModels:
    def generate_content(self, **kwargs):
        return type("Response", (), {
            "text": json.dumps({
                "subjects": [{
                    "name": "DTSP",
                    "abbreviation": "DTSP",
                    "exam_date": "2026-11-01",
                    "priority": 5,
                    "difficulty": 4,
                    "confidence": 2,
                    "feeling": "anxious",
                    "estimated_remaining_hours": 12,
                    "units": [
                        {"number": 1, "name": "Signals", "status": "completed"},
                        {"number": 2, "name": "Systems", "status": "completed"},
                        {"number": 3, "name": "Transforms", "status": "not_started"},
                    ],
                    "notes": "",
                }],
                "tasks": [],
                "preferences": {},
                "assumptions": [],
                "missing_details": [],
            })
        })()


class FakeClient:
    models = FakeModels()


def test_study_ask_extracts_and_derives_values(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    result = GeminiPlanner(FakeClient()).extract_study_intake(
        "I have a DTSP exam on 1 November and finished two units.",
        "2026-10-26",
    )
    normalized = normalize_study_intake(result)
    subject = normalized["subjects"][0]
    assert subject["completed_units"] == 2
    assert subject["remaining_units"] == 1
    assert subject["days_left"] == 6

    counts = save_study_intake(JsonStore(tmp_path), normalized)
    assert counts == {"subjects_added": 1, "tasks_added": 0}
