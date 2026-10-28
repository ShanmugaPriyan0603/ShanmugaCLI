from __future__ import annotations

import json
import os
import shutil
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DATA_DIR, DATA_FILES, ensure_data_dir
from .errors import StorageError


DEFAULTS: dict[str, Any] = {
    "preferences": {},
    "subjects": [],
    "study_goals": [],
    "schedule": [],
    "progress": [],
    "commitments": [],
    "history": [],
}


class JsonStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        if name not in DATA_FILES:
            raise StorageError(f"Unknown data file: {name}")
        return self.data_dir / f"{name}.json"

    def load(self, name: str) -> Any:
        path = self.path(name)
        if not path.exists():
            value = deepcopy(DEFAULTS[name])
            self.save(name, value, backup=False)
            return value
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            corrupt = path.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.json")
            shutil.copy2(path, corrupt)
            raise StorageError(
                f"{path.name} is corrupt. A recovery copy was saved as {corrupt.name}."
            ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read {path}: {exc}") from exc

    def save(self, name: str, value: Any, backup: bool = True) -> None:
        path = self.path(name)
        if backup and path.exists():
            backup_path = path.with_suffix(f".backup-{datetime.now():%Y%m%d%H%M%S}.json")
            shutil.copy2(path, backup_path)
        fd, temporary = tempfile.mkstemp(prefix=f"{name}-", suffix=".tmp", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            os.replace(temporary, path)
        except OSError as exc:
            if os.path.exists(temporary):
                os.unlink(temporary)
            raise StorageError(f"Could not save {path}: {exc}") from exc

    def export_all(self) -> dict[str, Any]:
        return {name: self.load(name) for name in DATA_FILES}
