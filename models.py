"""Data models for the Todo List application."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class Priority(IntEnum):
    """Priority levels, highest value = most important."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1

    @property
    def label(self) -> str:
        labels = {
            Priority.CRITICAL: "危急",
            Priority.HIGH: "高",
            Priority.MEDIUM: "中",
            Priority.LOW: "低",
            Priority.TRIVIAL: "琐碎",
        }
        return labels[self]

    @property
    def color(self) -> str:
        colors = {
            Priority.CRITICAL: "#E53935",
            Priority.HIGH: "#FB8C00",
            Priority.MEDIUM: "#FDD835",
            Priority.LOW: "#43A047",
            Priority.TRIVIAL: "#78909C",
        }
        return colors[self]


@dataclass
class TodoItem:
    """A single todo item."""

    text: str
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    item_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.item_id,
            "text": self.text,
            "priority": int(self.priority),
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TodoItem:
        return cls(
            text=d["text"],
            priority=Priority(d["priority"]),
            completed=d.get("completed", False),
            item_id=d.get("id", uuid.uuid4().hex[:8]),
            created_at=d.get("created_at", datetime.now().isoformat()),
        )
