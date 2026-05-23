"""Test fixtures for the todo list test suite."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from models import Priority, TodoItem
from storage import TodoStorage

# Set test directory as working context so models/storage imports work
os.chdir(Path(__file__).resolve().parent.parent)


@pytest.fixture
def sample_items() -> list[TodoItem]:
    """A set of sample todo items with known priorities and states."""
    return [
        TodoItem(text="危急任务", priority=Priority.CRITICAL),
        TodoItem(text="高优先级任务", priority=Priority.HIGH),
        TodoItem(text="中优先级任务", priority=Priority.MEDIUM),
        TodoItem(text="低优先级任务", priority=Priority.LOW),
        TodoItem(text="琐碎任务", priority=Priority.TRIVIAL),
    ]


@pytest.fixture
def mixed_items() -> list[TodoItem]:
    """Sample items in random order, some completed."""
    items = [
        TodoItem(text="A-中", priority=Priority.MEDIUM),
        TodoItem(text="B-高-已完成", priority=Priority.HIGH, completed=True),
        TodoItem(text="C-危急", priority=Priority.CRITICAL),
        TodoItem(text="D-低-已完成", priority=Priority.LOW, completed=True),
        TodoItem(text="E-琐碎", priority=Priority.TRIVIAL),
    ]
    return items


@pytest.fixture
def temp_storage() -> TodoStorage:
    """TodoStorage pointing to a temporary file (auto-cleanup)."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    storage = TodoStorage(filepath=path)
    yield storage
    # Cleanup
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def temp_json_file() -> str:
    """Create a temporary JSON file with known content, return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass
