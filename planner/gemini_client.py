from __future__ import annotations

import json
import time
from typing import Any

from .config import api_key, model_name
from .errors import GeminiError
from .schemas import PROPOSAL_SCHEMA, STUDY_INTAKE_SCHEMA


class GeminiPlanner:
    def __init__(self, client: Any = None):
        self._client = client

    def propose(self, context: dict[str, Any]) -> dict[str, Any]:
        if not api_key():
            raise GeminiError("GEMINI_API_KEY is not configured; use local scheduling or set the environment variable.")
        try:
            if self._client is None:
                from google import genai
                self._client = genai.Client(api_key=api_key())
            response = self._client.models.generate_content(
                model=model_name(),
                contents=json.dumps(context),
                config={"response_mime_type": "application/json", "response_schema": PROPOSAL_SCHEMA},
            )
            result = json.loads(response.text)
            if not isinstance(result, dict) or not isinstance(result.get("blocks"), list):
                raise GeminiError("Gemini returned an invalid planning proposal.")
            return result
        except GeminiError:
            raise
        except Exception as exc:
            raise GeminiError("Gemini planning failed; the approved schedule was not changed.") from exc

    def extract_study_intake(self, text: str, today: str) -> dict[str, Any]:
        if not api_key():
            raise GeminiError("GEMINI_API_KEY is not configured; use the local commands or set the environment variable.")
        prompt = {
            "task": "Extract study-planner data from the user's free-form message.",
            "today": today,
            "rules": [
                "Return only the requested JSON structure.",
                "Never invent syllabus unit names, dates, hours, or feelings.",
                "Use null or an empty list when the user did not provide a value.",
                "Use ISO date format YYYY-MM-DD when a date is provided.",
                "Set each unit status to completed, in_progress, needs_revision, or not_started.",
                "Put uncertain interpretations in assumptions and absent important information in missing_details.",
                "The local application will calculate remaining units and time left; do not fabricate those values.",
            ],
            "user_message": text,
        }
        try:
            if self._client is None:
                from google import genai
                self._client = genai.Client(api_key=api_key())
            response = None
            for attempt in range(2):
                try:
                    response = self._client.models.generate_content(
                        model=model_name(),
                        contents=json.dumps(prompt),
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": STUDY_INTAKE_SCHEMA,
                        },
                    )
                    break
                except Exception as exc:
                    message = str(exc)
                    transient = any(code in message for code in ("429", "500", "502", "503", "504"))
                    if not transient or attempt == 1:
                        raise
                    time.sleep(1)
            if response is None:
                raise GeminiError("Gemini did not return a study intake response.")
            result = json.loads(response.text)
            if not isinstance(result, dict) or not isinstance(result.get("subjects"), list):
                raise GeminiError("Gemini returned an invalid study intake.")
            return result
        except GeminiError:
            raise
        except Exception as exc:
            message = str(exc)
            if "404" in message or "NOT_FOUND" in message:
                detail = f"Gemini model '{model_name()}' is unavailable. Set GEMINI_MODEL to an available model."
            elif "401" in message or "403" in message or "UNAUTHENTICATED" in message:
                detail = "Gemini rejected the API key. Check planner/.env.local or GEMINI_API_KEY."
            elif any(code in message for code in ("429", "quota", "RESOURCE_EXHAUSTED")):
                detail = "Gemini rate limit or quota reached. Try again later."
            elif "503" in message or "UNAVAILABLE" in message:
                detail = "Gemini is temporarily unavailable after one retry. Try again later."
            else:
                detail = "Study intake processing failed; no planner data was changed."
            raise GeminiError(detail) from exc
