class PlannerError(Exception):
    """Expected user-facing planner error."""


class StorageError(PlannerError):
    """Persistent data could not be read or written safely."""


class ValidationError(PlannerError):
    """A record or proposed schedule is invalid."""


class GeminiError(PlannerError):
    """An optional Gemini planning request failed."""
