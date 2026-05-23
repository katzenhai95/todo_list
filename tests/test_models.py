"""Tests for models.py — Priority enum and TodoItem dataclass."""

from __future__ import annotations

import pytest

from models import Priority, TodoItem


# ------------------------------------------------------------------ #
#  Priority Enum
# ------------------------------------------------------------------ #

class TestPriority:
    """TC-F001 / TC-F003: Priority enum correctness."""

    def test_values_are_ordered(self) -> None:
        """Higher priority value = more important."""
        assert Priority.CRITICAL > Priority.HIGH
        assert Priority.HIGH > Priority.MEDIUM
        assert Priority.MEDIUM > Priority.LOW
        assert Priority.LOW > Priority.TRIVIAL

    def test_int_conversion(self) -> None:
        """Priority can be constructed from int and converted back."""
        for p in Priority:
            assert Priority(int(p)) == p

    def test_label_is_non_empty(self) -> None:
        """Every priority has a Chinese label."""
        for p in Priority:
            assert p.label
            assert isinstance(p.label, str)
            assert len(p.label) > 0

    def test_color_is_hex(self) -> None:
        """Every priority has a valid hex color."""
        for p in Priority:
            assert p.color.startswith("#")
            assert len(p.color) == 7

    def test_sort_order_descending(self) -> None:
        """Sorted by priority descending yields CRITICAL first, TRIVIAL last."""
        priorities = list(Priority)
        priorities.sort(reverse=True)
        assert priorities[0] == Priority.CRITICAL
        assert priorities[-1] == Priority.TRIVIAL


# ------------------------------------------------------------------ #
#  TodoItem
# ------------------------------------------------------------------ #

class TestTodoItem:
    """TC-F001 / TC-F004: TodoItem creation, serialization, state toggling."""

    def test_create_item_defaults(self) -> None:
        item = TodoItem(text="测试条目")
        assert item.text == "测试条目"
        assert item.priority == Priority.MEDIUM
        assert item.completed is False
        assert len(item.item_id) == 8
        assert item.created_at  # non-empty timestamp

    def test_create_item_with_priority(self) -> None:
        item = TodoItem(text="高优", priority=Priority.HIGH)
        assert item.priority == Priority.HIGH

    def test_to_dict_round_trip(self) -> None:
        """Item serialized then deserialized should be equivalent."""
        original = TodoItem(text="往返测试", priority=Priority.CRITICAL, completed=True)
        d = original.to_dict()
        restored = TodoItem.from_dict(d)
        assert restored.text == original.text
        assert restored.priority == original.priority
        assert restored.completed == original.completed
        assert restored.item_id == original.item_id

    def test_from_dict_missing_fields(self) -> None:
        """from_dict should handle missing optional fields gracefully."""
        item = TodoItem.from_dict({"text": "最小字段", "priority": 5})
        assert item.text == "最小字段"
        assert item.priority == Priority.CRITICAL
        assert item.completed is False
        assert len(item.item_id) == 8

    def test_toggle_completed(self) -> None:
        """Completed flag can be toggled."""
        item = TodoItem(text="切换测试")
        assert item.completed is False
        item.completed = True
        assert item.completed is True
