"""JSON-based persistence for todo items."""

from __future__ import annotations

import json
import os
from typing import Sequence

from models import TodoItem


DEFAULT_FILENAME = "todos.json"


class TodoStorage:
    """Handles loading and saving todo items to/from JSON."""

    def __init__(self, filepath: str | None = None) -> None:
        self.filepath: str = filepath or self._default_path()

    @staticmethod
    def _default_path() -> str:
        """Default save location next to the script."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_FILENAME)

    # ------------------------------------------------------------------ #
    #  Load / Save
    # ------------------------------------------------------------------ #

    def load(self) -> list[TodoItem]:
        """Load todo items from the JSON file. Returns empty list if file missing."""
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [TodoItem.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    def save(self, items: Sequence[TodoItem]) -> None:
        """Save todo items to the JSON file."""
        data = [item.to_dict() for item in items]
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ #
    #  Export / Import
    # ------------------------------------------------------------------ #

    def export_to(self, items: Sequence[TodoItem], filepath: str) -> None:
        """Export items to an arbitrary file path."""
        data = [item.to_dict() for item in items]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from(self, filepath: str) -> list[TodoItem]:
        """Import items from an arbitrary file path."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [TodoItem.from_dict(item) for item in data]
