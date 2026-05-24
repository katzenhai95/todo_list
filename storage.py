"""JSON-based persistence for todo items.

Uses %APPDATA%/TodoList/ for storage so persistence works both in
development and when packaged as a PyInstaller executable.
"""

from __future__ import annotations

import json
import os
from typing import Sequence

from models import TodoItem


DEFAULT_FILENAME = "todos.json"


def _data_dir() -> str:
    """Get the persistent data directory. Creates it if missing."""
    base = os.environ.get("APPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "TodoList")
    os.makedirs(path, exist_ok=True)
    return path


class TodoStorage:
    """Handles loading and saving todo items to/from JSON."""

    def __init__(self, filepath: str | None = None) -> None:
        self.filepath: str = filepath or os.path.join(_data_dir(), DEFAULT_FILENAME)

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
