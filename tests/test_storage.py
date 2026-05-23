"""Tests for storage.py — JSON persistence, export, import."""

from __future__ import annotations

import json
import os

import pytest

from models import Priority, TodoItem
from storage import TodoStorage


class TestStorageSaveLoad:
    """TC-F006: Data persistence — save and reload cycle."""

    def test_save_and_load_round_trip(self, temp_storage: TodoStorage) -> None:
        items = [
            TodoItem(text="条目一", priority=Priority.HIGH),
            TodoItem(text="条目二", priority=Priority.LOW, completed=True),
        ]
        temp_storage.save(items)
        loaded = temp_storage.load()
        assert len(loaded) == 2
        assert loaded[0].text == "条目一"
        assert loaded[0].priority == Priority.HIGH
        assert loaded[1].text == "条目二"
        assert loaded[1].completed is True

    def test_load_empty_when_file_missing(self, temp_storage: TodoStorage) -> None:
        """TC-F006-02: First launch — empty file → empty list, no crash."""
        # Ensure file doesn't exist
        if os.path.exists(temp_storage.filepath):
            os.remove(temp_storage.filepath)
        items = temp_storage.load()
        assert items == []

    def test_load_handles_corrupt_json(self, temp_storage: TodoStorage) -> None:
        """Corrupt JSON should return empty list, not crash."""
        with open(temp_storage.filepath, "w", encoding="utf-8") as f:
            f.write("{invalid json!!!")
        items = temp_storage.load()
        assert items == []

    def test_save_creates_file(self, temp_storage: TodoStorage) -> None:
        """Saving creates the file on disk."""
        if os.path.exists(temp_storage.filepath):
            os.remove(temp_storage.filepath)
        temp_storage.save([TodoItem(text="x")])
        assert os.path.exists(temp_storage.filepath)

    def test_save_overwrites(self, temp_storage: TodoStorage) -> None:
        """Second save replaces first, no data duplication."""
        temp_storage.save([TodoItem(text="第一版")])
        temp_storage.save([TodoItem(text="第二版")])
        loaded = temp_storage.load()
        assert len(loaded) == 1
        assert loaded[0].text == "第二版"


class TestStorageExport:
    """TC-F007: Export to file."""

    def test_export_produces_valid_json(self, temp_storage: TodoStorage, temp_json_file: str) -> None:
        items = [TodoItem(text="导出条目", priority=Priority.CRITICAL)]
        temp_storage.export_to(items, temp_json_file)
        with open(temp_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["text"] == "导出条目"
        assert data[0]["priority"] == 5

    def test_export_empty_list(self, temp_storage: TodoStorage, temp_json_file: str) -> None:
        temp_storage.export_to([], temp_json_file)
        with open(temp_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == []


class TestStorageImport:
    """TC-F008: Import from file — replace, merge, invalid file."""

    def test_import_replace(self, temp_storage: TodoStorage, temp_json_file: str) -> None:
        """Importing replaces current data."""
        data = [
            {"text": "外部条目", "priority": 3, "completed": False},
        ]
        with open(temp_json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        imported = temp_storage.import_from(temp_json_file)
        assert len(imported) == 1
        assert imported[0].text == "外部条目"

    def test_import_invalid_file_raises(self, temp_storage: TodoStorage, temp_json_file: str) -> None:
        """Importing a non-existent file raises FileNotFoundError."""
        os.remove(temp_json_file)
        with pytest.raises(FileNotFoundError):
            temp_storage.import_from(temp_json_file)

    def test_import_bad_json_raises(self, temp_storage: TodoStorage, temp_json_file: str) -> None:
        """Importing a malformed JSON file raises json.JSONDecodeError."""
        with open(temp_json_file, "w", encoding="utf-8") as f:
            f.write("not json")
        with pytest.raises(json.JSONDecodeError):
            temp_storage.import_from(temp_json_file)
