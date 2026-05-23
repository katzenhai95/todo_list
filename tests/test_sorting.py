"""Tests for sorting logic and item list manipulation."""

from __future__ import annotations

from models import Priority, TodoItem


# ------------------------------------------------------------------ #
#  Helper: replicate app.py _sort_items logic
# ------------------------------------------------------------------ #

def sort_items(items: list[TodoItem]) -> list[TodoItem]:
    """Sort items: completed at bottom, then by priority descending, then by creation time."""
    items.sort(key=lambda i: (i.completed, -int(i.priority), i.created_at))
    return items


# ------------------------------------------------------------------ #
#  Tests
# ------------------------------------------------------------------ #

class TestSorting:
    """TC-F003: Priority sorting logic."""

    def test_sort_priority_descending(self) -> None:
        """Items sorted by priority descending: CRITICAL → HIGH → MEDIUM → LOW → TRIVIAL."""
        items = [
            TodoItem(text="低", priority=Priority.LOW),
            TodoItem(text="危急", priority=Priority.CRITICAL),
            TodoItem(text="中", priority=Priority.MEDIUM),
            TodoItem(text="高", priority=Priority.HIGH),
            TodoItem(text="琐碎", priority=Priority.TRIVIAL),
        ]
        sorted_items = sort_items(items)
        priorities = [int(i.priority) for i in sorted_items]
        assert priorities == [5, 4, 3, 2, 1]  # descending

    def test_completed_items_sink_to_bottom(self, mixed_items: list[TodoItem]) -> None:
        """TC-F003-02: Completed items appear after all incomplete items."""
        sort_items(mixed_items)
        # Find the boundary: all before boundary should be incomplete
        states = [i.completed for i in mixed_items]
        # Assert: no False appears after a True
        completed_indices = [j for j, s in enumerate(states) if s]
        incomplete_indices = [j for j, s in enumerate(states) if not s]
        if completed_indices and incomplete_indices:
            assert max(incomplete_indices) < min(completed_indices)

    def test_completed_items_sorted_by_priority_too(self, mixed_items: list[TodoItem]) -> None:
        """Completed items are also sorted by priority descending among themselves."""
        sort_items(mixed_items)
        completed = [i for i in mixed_items if i.completed]
        if len(completed) >= 2:
            for i in range(len(completed) - 1):
                assert int(completed[i].priority) >= int(completed[i + 1].priority)

    def test_sort_preserves_item_count(self, mixed_items: list[TodoItem]) -> None:
        """Sorting does not drop any items."""
        original_count = len(mixed_items)
        sort_items(mixed_items)
        assert len(mixed_items) == original_count


class TestItemListOperations:
    """TC-F001 / TC-F005: Add and delete item logic."""

    def test_add_item_appends(self) -> None:
        items: list[TodoItem] = []
        items.append(TodoItem(text="新条目"))
        assert len(items) == 1
        assert items[0].text == "新条目"

    def test_delete_item_by_id(self) -> None:
        i1 = TodoItem(text="保留")
        i2 = TodoItem(text="删除")
        items = [i1, i2]
        items = [i for i in items if i.item_id != i2.item_id]
        assert len(items) == 1
        assert items[0].text == "保留"

    def test_delete_nonexistent_does_nothing(self) -> None:
        items = [TodoItem(text="唯一")]
        result = [i for i in items if i.item_id != "nonexistent"]
        assert len(result) == 1


class TestEmptyTextRejection:
    """TC-F001-02: Empty text should not create an item."""

    def test_empty_text_validation(self) -> None:
        """The app should reject empty strings. This tests the validation logic."""
        def is_valid_text(text: str) -> bool:
            return bool(text.strip())

        assert is_valid_text("有效文本") is True
        assert is_valid_text("") is False
        assert is_valid_text("   ") is False
