PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "blocks": {"type": "array", "items": {"type": "object"}},
        "unscheduled_tasks": {"type": "array", "items": {"type": "object"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["blocks", "unscheduled_tasks", "assumptions"],
}

STUDY_INTAKE_SCHEMA = {
    "type": "object",
    "properties": {
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "abbreviation": {"type": "string"},
                    "exam_date": {"type": "string", "nullable": True},
                    "priority": {"type": "integer"},
                    "difficulty": {"type": "integer"},
                    "confidence": {"type": "integer"},
                    "feeling": {"type": "string"},
                    "estimated_remaining_hours": {"type": "number"},
                    "units": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "number": {"type": "integer"},
                                "name": {"type": "string"},
                                "status": {"type": "string"},
                            },
                            "required": ["number", "name", "status"],
                        },
                    },
                    "notes": {"type": "string"},
                },
                "required": [
                    "name",
                    "abbreviation",
                    "exam_date",
                    "priority",
                    "difficulty",
                    "confidence",
                    "feeling",
                    "estimated_remaining_hours",
                    "units",
                    "notes",
                ],
            },
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject_name": {"type": "string"},
                    "description": {"type": "string"},
                    "deadline": {"type": "string", "nullable": True},
                    "estimated_minutes": {"type": "integer"},
                    "priority": {"type": "integer"},
                },
                "required": [
                    "subject_name",
                    "description",
                    "deadline",
                    "estimated_minutes",
                    "priority",
                ],
            },
        },
        "preferences": {"type": "object"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "missing_details": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["subjects", "tasks", "preferences", "assumptions", "missing_details"],
}
