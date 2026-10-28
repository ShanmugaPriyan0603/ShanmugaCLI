import json

import pytest

from planner.errors import StorageError
from planner.storage import JsonStore


def test_storage_creates_and_round_trips(tmp_path):
    store = JsonStore(tmp_path)
    assert store.load("subjects") == []
    store.save("subjects", [{"name": "Math"}])
    assert store.load("subjects") == [{"name": "Math"}]
    assert list(tmp_path.glob("subjects.backup-*.json"))


def test_corrupt_json_is_preserved(tmp_path):
    path = tmp_path / "subjects.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(StorageError):
        JsonStore(tmp_path).load("subjects")
    assert list(tmp_path.glob("subjects.corrupt-*.json"))
