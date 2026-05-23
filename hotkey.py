"""Global hotkey management using pynput."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Callable

from pynput.keyboard import Key, KeyCode, Listener


@dataclass
class Hotkey:
    """Represents a hotkey combination."""

    modifiers: set[str]  # e.g. {"ctrl", "alt", "shift"}
    key: str             # e.g. "t", "n", "F1"

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


class HotkeyManager:
    """Manages a single global hotkey using pynput.

    Listens globally and fires a callback when the configured combination
    is pressed.
    """

    CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "hotkey_config.json"
    )

    def __init__(self) -> None:
        self._hotkey = self._load_config()
        self._callback: Callable[[], None] | None = None
        self._listener: Listener | None = None
        self._pressed: set[str] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def start(self, callback: Callable[[], None]) -> None:
        """Start listening for the hotkey. Callback runs on press."""
        self._callback = callback
        self._listener = Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    def set_hotkey(self, modifiers: set[str], key: str) -> None:
        """Update the hotkey combination and persist to config."""
        self._hotkey = Hotkey(modifiers=modifiers, key=key)
        self._save_config(self._hotkey)

    def get_hotkey(self) -> Hotkey:
        return self._hotkey

    # ------------------------------------------------------------------ #
    #  Listener callbacks
    # ------------------------------------------------------------------ #

    def _on_press(self, key: Key | KeyCode | None) -> None:
        if key is None:
            return

        name = self._key_name(key)
        with self._lock:
            self._pressed.add(name)

        if self._match():
            self._pressed.clear()  # prevent re-trigger
            if self._callback:
                # Schedule on main thread via tkinter's after
                self._callback()

    def _on_release(self, key: Key | KeyCode | None) -> None:
        if key is None:
            return
        name = self._key_name(key)
        with self._lock:
            self._pressed.discard(name)

    # ------------------------------------------------------------------ #
    #  Matching
    # ------------------------------------------------------------------ #

    def _match(self) -> bool:
        """Check if currently pressed keys match the configured hotkey."""
        expected = self._hotkey.modifiers | {self._hotkey.key}
        with self._lock:
            return expected == self._pressed

    # ------------------------------------------------------------------ #
    #  Key name conversion
    # ------------------------------------------------------------------ #

    @staticmethod
    def _key_name(key: Key | KeyCode) -> str:
        if isinstance(key, KeyCode):
            ch = key.char
            return ch.lower() if ch else f"<{key.vk}>"
        # Special keys
        mapping = {
            Key.ctrl: "ctrl",
            Key.ctrl_l: "ctrl",
            Key.ctrl_r: "ctrl",
            Key.alt: "alt",
            Key.alt_l: "alt",
            Key.alt_r: "alt",
            Key.shift: "shift",
            Key.shift_l: "shift",
            Key.shift_r: "shift",
            Key.cmd: "win",
            Key.cmd_l: "win",
            Key.cmd_r: "win",
            Key.tab: "tab",
            Key.enter: "enter",
            Key.esc: "esc",
            Key.space: "space",
            Key.backspace: "backspace",
            Key.delete: "delete",
            Key.up: "up",
            Key.down: "down",
            Key.left: "left",
            Key.right: "right",
            Key.f1: "f1", Key.f2: "f2", Key.f3: "f3", Key.f4: "f4",
            Key.f5: "f5", Key.f6: "f6", Key.f7: "f7", Key.f8: "f8",
            Key.f9: "f9", Key.f10: "f10", Key.f11: "f11", Key.f12: "f12",
        }
        return mapping.get(key, str(key))

    # ------------------------------------------------------------------ #
    #  Config persistence
    # ------------------------------------------------------------------ #

    def _load_config(self) -> Hotkey:
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                    return Hotkey.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError):
                pass
        return Hotkey.default()

    def _save_config(self, hotkey: Hotkey) -> None:
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(hotkey.to_dict(), f, indent=2)
