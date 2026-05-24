"""Global hotkey management using the 'keyboard' library."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Callable

import keyboard

_log = logging.getLogger(__name__)


@dataclass
class Hotkey:
    modifiers: set[str]
    key: str

    @classmethod
    def default(cls) -> Hotkey:
        return cls(modifiers={"ctrl"}, key="t")

    def to_dict(self) -> dict:
        return {"modifiers": sorted(self.modifiers), "key": self.key}

    @classmethod
    def from_dict(cls, d: dict) -> Hotkey:
        return cls(modifiers=set(d["modifiers"]), key=d["key"])

    @property
    def display(self) -> str:
        parts = sorted(self.modifiers) + [self.key]
        return "+".join(p.upper() for p in parts)

    def to_keyboard_str(self) -> str:
        """Convert to 'keyboard' library format, e.g. 'ctrl+t'."""
        return "+".join(sorted(self.modifiers) + [self.key])


class HotkeyManager:
    """Global hotkey using the 'keyboard' library."""

    CONFIG_FILENAME = "hotkey_config.json"

    @staticmethod
    def _config_path() -> str:
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        path = os.path.join(base, "TodoList")
        os.makedirs(path, exist_ok=True)
        return os.path.join(path, HotkeyManager.CONFIG_FILENAME)

    def __init__(self) -> None:
        self._hotkey = self._load_config()
        self._callback: Callable[[], None] | None = None
        self._registered = False

    def start(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._register()

    def stop(self) -> None:
        self._unregister()
        self._callback = None

    def set_hotkey(self, modifiers: set[str], key: str) -> None:
        was_running = self._registered
        self._unregister()
        self._hotkey = Hotkey(modifiers=modifiers, key=key)
        self._save_config(self._hotkey)
        if was_running:
            self._register()

    def get_hotkey(self) -> Hotkey:
        return self._hotkey

    def _register(self) -> None:
        if self._registered:
            return
        try:
            keyboard.add_hotkey(
                self._hotkey.to_keyboard_str(), self._on_trigger
            )
            self._registered = True
            _log.info("Hotkey registered: %s", self._hotkey.display)
        except Exception as e:
            _log.error("Failed to register hotkey: %s", e)

    def _unregister(self) -> None:
        if self._registered:
            try:
                keyboard.remove_hotkey(self._hotkey.to_keyboard_str())
            except Exception:
                keyboard.clear_all_hotkeys()
            self._registered = False

    def _on_trigger(self) -> None:
        _log.info("Hotkey triggered: %s", self._hotkey.display)
        if self._callback:
            try:
                self._callback()
            except Exception as e:
                _log.error("Hotkey callback failed: %s", e)

    def _load_config(self) -> Hotkey:
        path = self._config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return Hotkey.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError):
                pass
        return Hotkey.default()

    def _save_config(self, hotkey: Hotkey) -> None:
        with open(self._config_path(), "w", encoding="utf-8") as f:
            json.dump(hotkey.to_dict(), f, indent=2)
