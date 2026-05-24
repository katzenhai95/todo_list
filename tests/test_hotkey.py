"""Tests for hotkey.py — Hotkey dataclass and HotkeyManager config persistence."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from hotkey import Hotkey, HotkeyManager


class TestHotkeyDataclass:
    """TC-F002 / TC-F011: Hotkey serialization and display."""

    def test_default_hotkey(self) -> None:
        hk = Hotkey.default()
        assert hk.modifiers == {"ctrl"}
        assert hk.key == "t"

    def test_display_format(self) -> None:
        hk = Hotkey(modifiers={"ctrl", "shift"}, key="n")
        assert hk.display == "CTRL+SHIFT+N"

    def test_to_dict_from_dict_round_trip(self) -> None:
        original = Hotkey(modifiers={"alt", "ctrl"}, key="f1")
        d = original.to_dict()
        restored = Hotkey.from_dict(d)
        assert restored.modifiers == original.modifiers
        assert restored.key == original.key

    def test_to_dict_modifiers_are_sorted(self) -> None:
        hk = Hotkey(modifiers={"shift", "ctrl", "alt"}, key="k")
        d = hk.to_dict()
        assert d["modifiers"] == ["alt", "ctrl", "shift"]


class TestHotkeyManagerConfig:
    """TC-F011 / TC-F012: Hotkey config save/load/persistence."""

    @pytest.fixture
    def temp_config_dir(self, monkeypatch) -> str:
        """Create a temp directory and monkey-patch _config_path."""
        import hotkey as hk_mod

        td = tempfile.mkdtemp()
        config_path = os.path.join(td, "hotkey_config.json")
        monkeypatch.setattr(hk_mod.HotkeyManager, "_config_path", staticmethod(lambda: config_path))
        yield td
        try:
            os.remove(os.path.join(td, "hotkey_config.json"))
            os.rmdir(td)
        except OSError:
            pass

    def test_default_when_no_config(self, temp_config_dir: str) -> None:
        """TC-F012: First launch gets default hotkey."""
        mgr = HotkeyManager()
        hk = mgr.get_hotkey()
        assert hk.modifiers == {"ctrl"}
        assert hk.key == "t"

    def test_set_and_get_hotkey(self, temp_config_dir: str) -> None:
        """TC-F011: Custom hotkey is stored and retrievable."""
        mgr = HotkeyManager()
        mgr.set_hotkey(modifiers={"ctrl", "shift"}, key="n")
        hk = mgr.get_hotkey()
        assert hk.modifiers == {"ctrl", "shift"}
        assert hk.key == "n"

    def test_config_persisted_to_disk(self, temp_config_dir: str) -> None:
        """TC-F012: Hotkey saved to config file survives new manager instance."""
        mgr = HotkeyManager()
        mgr.set_hotkey(modifiers={"alt"}, key="x")

        # Create a new manager → should load from saved config
        mgr2 = HotkeyManager()
        hk = mgr2.get_hotkey()
        assert hk.modifiers == {"alt"}
        assert hk.key == "x"

    def test_config_file_is_valid_json(self, temp_config_dir: str) -> None:
        """Config file contains valid JSON with expected structure."""
        mgr = HotkeyManager()
        mgr.set_hotkey(modifiers={"ctrl"}, key="t")

        import hotkey as hk_mod
        with open(mgr._config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "modifiers" in data
        assert "key" in data
        assert isinstance(data["modifiers"], list)
