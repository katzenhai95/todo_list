"""Main application UI using customtkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from edge import EdgeManager
from hotkey import HotkeyManager
from models import Priority, TodoItem
from storage import TodoStorage

# ------------------------------------------------------------------ #
#  Theme
# ------------------------------------------------------------------ #

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PRIORITY_LABELS = {p.label: p for p in Priority}
PRIORITY_LABELS_REVERSE = {p: p.label for p in Priority}


# ------------------------------------------------------------------ #
#  Quick-Add Popup
# ------------------------------------------------------------------ #

class QuickAddPopup(ctk.CTkToplevel):
    """Small popup window for quickly adding a todo item via hotkey."""

    def __init__(self, master: ctk.CTk, on_add: Callable[[str, Priority], None]) -> None:
        super().__init__(master)
        self._on_add = on_add

        self.title("快速添加")
        self.geometry("360x160")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 360) // 2
        y = (sh - 160) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

        # Focus entry and bind Enter
        self._entry.focus_set()
        self.bind("<Return>", lambda _e: self._do_add())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build_ui(self) -> None:
        # Priority selector
        self._priority_var = ctk.StringVar(value=Priority.MEDIUM.label)
        ctk.CTkLabel(self, text="优先级:").pack(pady=(12, 2))
        self._priority_menu = ctk.CTkOptionMenu(
            self,
            values=[p.label for p in sorted(Priority, reverse=True)],
            variable=self._priority_var,
        )
        self._priority_menu.pack(pady=(0, 6))

        # Text entry
        self._entry = ctk.CTkEntry(self, placeholder_text="输入待办事项...", width=300)
        self._entry.pack(pady=(0, 10))

        # Add button
        ctk.CTkButton(self, text="添加 (Enter)", command=self._do_add, width=120).pack()

    def _do_add(self) -> None:
        text = self._entry.get().strip()
        if not text:
            return
        priority = PRIORITY_LABELS[self._priority_var.get()]
        self._on_add(text, priority)
        self.destroy()


# ------------------------------------------------------------------ #
#  Settings Dialog
# ------------------------------------------------------------------ #

class SettingsDialog(ctk.CTkToplevel):
    """Dialog for customizing the hotkey."""

    MODIFIER_KEYS = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "win": "Win"}
    VALID_MODIFIERS = set(MODIFIER_KEYS.keys())

    def __init__(
        self,
        master: ctk.CTk,
        hotkey_manager: HotkeyManager,
        on_save: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._hotkey_manager = hotkey_manager
        self._on_save = on_save
        self._recording = False
        self._recorded_modifiers: set[str] = set()
        self._recorded_key = ""

        self.title("设置")
        self.geometry("380x280")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._build_ui()

    def _build_ui(self) -> None:
        current = self._hotkey_manager.get_hotkey()

        ctk.CTkLabel(self, text="快捷键设置", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(16, 4)
        )

        # Current hotkey display
        self._current_label = ctk.CTkLabel(
            self,
            text=f"当前快捷键: {current.display}",
            font=ctk.CTkFont(size=14),
        )
        self._current_label.pack(pady=(4, 8))

        # Record button
        self._record_btn = ctk.CTkButton(
            self,
            text="录制新快捷键",
            command=self._start_recording,
            width=160,
        )
        self._record_btn.pack(pady=(4, 8))

        # Recording status
        self._status_label = ctk.CTkLabel(self, text="", text_color="#FDD835")
        self._status_label.pack(pady=(2, 0))

        # Instruction
        ctk.CTkLabel(
            self,
            text="点击\"录制\"后，按下你想要的组合键。\n必须包含至少一个修饰键 (Ctrl/Alt/Shift/Win)。",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(8, 12))

        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(btn_frame, text="保存", command=self._save, width=100).pack(
            side="left", padx=(20, 0)
        )
        ctk.CTkButton(
            btn_frame, text="取消", command=self.destroy, width=100, fg_color="gray"
        ).pack(side="right", padx=(0, 20))

        # Bind keys for recording
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<KeyRelease>", self._on_key_release)

    def _start_recording(self) -> None:
        self._recording = True
        self._recorded_modifiers.clear()
        self._recorded_key = ""
        self._record_btn.configure(text="录制中...", state="disabled")
        self._status_label.configure(text="请按下组合键...")
        self.focus_set()

    def _on_key_press(self, event: tk.Event) -> None:
        if not self._recording:
            return
        name = self._event_to_name(event)
        if name in self.VALID_MODIFIERS:
            self._recorded_modifiers.add(name)
        else:
            self._recorded_key = name
        self._update_status()

    def _on_key_release(self, event: tk.Event) -> None:
        if not self._recording:
            return
        # When all modifiers are released and we have a key, consider recording done
        modifiers_down = {self._event_to_name(event)}
        if not (self._recorded_modifiers - modifiers_down) and self._recorded_key:
            self._finish_recording()

    def _update_status(self) -> None:
        parts = sorted(self._recorded_modifiers) + ([self._recorded_key] if self._recorded_key else [])
        if parts:
            self._status_label.configure(text=f"已按下: {'+'.join(p.upper() for p in parts)}")

    def _finish_recording(self) -> None:
        if not self._recorded_key:
            self._status_label.configure(text="请按下一个普通键 (如 T、N、F1)")
            return
        if not self._recorded_modifiers:
            self._status_label.configure(
                text="必须包含至少一个修饰键 (Ctrl/Alt/Shift/Win)"
            )
            self._recording = True
            return

        self._recording = False
        hk = self._hotkey_manager.get_hotkey()
        parts = sorted(self._recorded_modifiers) + [self._recorded_key]
        self._current_label.configure(text=f"当前快捷键: {'+'.join(p.upper() for p in parts)}")
        self._status_label.configure(text="录制完成")
        self._record_btn.configure(text="重新录制", state="normal")
        self._current_label.configure(
            text=f"新快捷键: {'+'.join(p.upper() for p in parts)}"
        )

    def _save(self) -> None:
        if self._recorded_modifiers and self._recorded_key:
            self._hotkey_manager.set_hotkey(self._recorded_modifiers, self._recorded_key)
            self._on_save()
        self.destroy()

    @staticmethod
    def _event_to_name(event: tk.Event) -> str:
        """Convert a tkinter key event to a normalized name."""
        keysym = event.keysym.lower()
        mapping = {
            "control_l": "ctrl",
            "control_r": "ctrl",
            "alt_l": "alt",
            "alt_r": "alt",
            "shift_l": "shift",
            "shift_r": "shift",
            "meta_l": "win",
            "meta_r": "win",
        }
        if keysym in mapping:
            return mapping[keysym]
        # For regular keys, return the keysym in lowercase
        if len(keysym) == 1:
            return keysym
        # Function keys etc.
        return keysym


# ------------------------------------------------------------------ #
#  Todo Item Widget
# ------------------------------------------------------------------ #

class TodoItemWidget(ctk.CTkFrame):
    """A single row in the todo list."""

    def __init__(
        self,
        master: ctk.CTkFrame,
        item: TodoItem,
        on_delete: Callable[[TodoItemWidget], None],
        on_toggle: Callable[[TodoItemWidget], None],
    ) -> None:
        super().__init__(master, fg_color="#2B2B2B", corner_radius=6)
        self.item = item
        self._on_delete = on_delete
        self._on_toggle = on_toggle

        self._build_ui()
        self._update_style()

    def _build_ui(self) -> None:
        # Priority indicator (colored bar)
        color = self.item.priority.color
        self._priority_bar = ctk.CTkFrame(self, width=6, fg_color=color, corner_radius=0)
        self._priority_bar.pack(side="left", fill="y", padx=(0, 8))

        # Priority label
        self._priority_label = ctk.CTkLabel(
            self,
            text=self.item.priority.label,
            width=36,
            font=ctk.CTkFont(size=11),
            text_color=self.item.priority.color,
        )
        self._priority_label.pack(side="left", padx=(0, 6))

        # Checkbox
        self._check_var = ctk.BooleanVar(value=self.item.completed)
        self._checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self._check_var,
            command=self._toggle,
            width=22,
        )
        self._checkbox.pack(side="left", padx=(0, 6))

        # Text
        self._text_label = ctk.CTkLabel(
            self,
            text=self.item.text,
            anchor="w",
            font=ctk.CTkFont(size=13),
        )
        self._text_label.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # Delete button
        self._del_btn = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#E53935",
            command=self._delete,
        )
        self._del_btn.pack(side="right", padx=(0, 4))

    def _toggle(self) -> None:
        self.item.completed = self._check_var.get()
        self._update_style()
        self._on_toggle(self)

    def _delete(self) -> None:
        self._on_delete(self)

    def _update_style(self) -> None:
        if self.item.completed:
            self._text_label.configure(
                text_color="gray",
                font=ctk.CTkFont(size=13, overstrike=True),
            )
        else:
            self._text_label.configure(
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=13),
            )


# ------------------------------------------------------------------ #
#  Main Application
# ------------------------------------------------------------------ #

class TodoApp(ctk.CTk):
    """Main todo list application window."""

    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 550

    def __init__(self) -> None:
        super().__init__()

        self.title("待办清单")
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(300, 350)
        self.resizable(True, True)

        # Position near top-right of screen
        sw = self.winfo_screenwidth()
        self.update_idletasks()
        self.geometry(f"+{sw - self.WINDOW_WIDTH - 40}+80")

        # Always on top
        self.attributes("-topmost", True)

        # Data
        self._storage = TodoStorage()
        self._items: list[TodoItem] = []
        self._item_widgets: dict[str, TodoItemWidget] = {}

        # Hotkey manager
        self._hotkey_manager = HotkeyManager()

        # Edge manager (auto-hide)
        self._edge_manager = EdgeManager(self)

        # Build UI
        self._build_ui()

        # Load saved data
        self._load_data()
        self._rebuild_list()

        # Start hotkey listener
        self._start_hotkey()

        # Save on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    #  UI Construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        # -- Toolbar --
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkButton(
            toolbar, text="导入", width=60, height=28, command=self._import
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            toolbar, text="导出", width=60, height=28, command=self._export
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            toolbar, text="设置", width=60, height=28, command=self._open_settings
        ).pack(side="left")

        # Current hotkey hint
        self._hotkey_hint = ctk.CTkLabel(
            toolbar,
            text=self._hotkey_manager.get_hotkey().display,
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        self._hotkey_hint.pack(side="right", padx=(0, 4))

        # -- Separator --
        ctk.CTkFrame(self, height=1, fg_color="gray").pack(fill="x", padx=8)

        # -- Scrollable list --
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        # -- Separator --
        ctk.CTkFrame(self, height=1, fg_color="gray").pack(fill="x", padx=8)

        # -- Add bar --
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=8, pady=(4, 8))

        self._priority_var = ctk.StringVar(value=Priority.MEDIUM.label)
        self._priority_menu = ctk.CTkOptionMenu(
            add_frame,
            values=[p.label for p in sorted(Priority, reverse=True)],
            variable=self._priority_var,
            width=60,
        )
        self._priority_menu.pack(side="left", padx=(0, 4))

        self._add_entry = ctk.CTkEntry(add_frame, placeholder_text="输入新待办...")
        self._add_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._add_entry.bind("<Return>", lambda _e: self._add_item())

        ctk.CTkButton(
            add_frame, text="添加", width=50, height=28, command=self._add_item
        ).pack(side="right")

    # ------------------------------------------------------------------ #
    #  Data operations
    # ------------------------------------------------------------------ #

    def _load_data(self) -> None:
        self._items = self._storage.load()

    def _save_data(self) -> None:
        # Sync widget state back to items
        for widget in self._item_widgets.values():
            widget.item.completed = widget._check_var.get()
        self._storage.save(self._items)

    def _add_item(self, text: str | None = None, priority: Priority | None = None) -> None:
        if text is None:
            text = self._add_entry.get().strip()
        if priority is None:
            priority = PRIORITY_LABELS[self._priority_var.get()]

        if not text:
            return

        item = TodoItem(text=text, priority=priority)
        self._items.append(item)
        self._sort_items()
        self._rebuild_list()
        self._save_data()

        # Clear entry
        self._add_entry.delete(0, "end")
        self._add_entry.focus_set()

    def _delete_item(self, widget: TodoItemWidget) -> None:
        item_id = widget.item.item_id
        self._items = [i for i in self._items if i.item_id != item_id]
        self._item_widgets.pop(item_id, None)
        widget.destroy()
        self._save_data()

    def _sort_items(self) -> None:
        """Sort items: completed at bottom, then by priority descending, then by creation time."""
        self._items.sort(
            key=lambda i: (i.completed, -int(i.priority), i.created_at)
        )

    def _rebuild_list(self) -> None:
        """Clear and rebuild the list UI from _items."""
        # Clear existing widgets
        for widget in self._item_widgets.values():
            widget.destroy()
        self._item_widgets.clear()

        for item in self._items:
            widget = TodoItemWidget(
                self._list_frame,
                item,
                on_delete=self._delete_item,
                on_toggle=lambda w: self._save_data(),
            )
            widget.pack(fill="x", pady=2)
            self._item_widgets[item.item_id] = widget

    # ------------------------------------------------------------------ #
    #  Import / Export
    # ------------------------------------------------------------------ #

    def _export(self) -> None:
        filepath = filedialog.asksaveasfilename(
            title="导出待办清单",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not filepath:
            return
        try:
            self._storage.export_to(self._items, filepath)
            messagebox.showinfo("导出成功", f"已导出到:\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _import(self) -> None:
        filepath = filedialog.askopenfilename(
            title="导入待办清单",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not filepath:
            return

        choice = messagebox.askyesnocancel(
            "导入模式",
            "是否替换当前列表？\n\n选择\"是\" = 替换\n选择\"否\" = 合并\n选择\"取消\" = 放弃导入",
        )
        if choice is None:
            return

        try:
            imported = self._storage.import_from(filepath)
        except Exception as e:
            messagebox.showerror("导入失败", str(e))
            return

        if choice:  # Replace
            self._items = imported
        else:  # Merge
            self._items.extend(imported)

        self._sort_items()
        self._rebuild_list()
        self._save_data()
        messagebox.showinfo("导入成功", f"已导入 {len(imported)} 条待办事项")

    # ------------------------------------------------------------------ #
    #  Quick-add (triggered by hotkey)
    # ------------------------------------------------------------------ #

    def quick_add(self) -> None:
        """Show the quick-add popup. Safe to call from any thread."""

        def _show() -> None:
            if not self.winfo_exists():
                return
            # Ensure window is visible
            self.deiconify()
            self.lift()
            self.focus_force()
            # Show popup
            QuickAddPopup(self, on_add=self._on_quick_add)

        self.after(0, _show)

    def _on_quick_add(self, text: str, priority: Priority) -> None:
        self._add_item(text, priority)

    # ------------------------------------------------------------------ #
    #  Hotkey management
    # ------------------------------------------------------------------ #

    def _start_hotkey(self) -> None:
        self._hotkey_manager.start(callback=self.quick_add)

    def _restart_hotkey(self) -> None:
        self._hotkey_manager.stop()
        self._start_hotkey()
        hk = self._hotkey_manager.get_hotkey()
        self._hotkey_hint.configure(text=hk.display)

    # ------------------------------------------------------------------ #
    #  Settings
    # ------------------------------------------------------------------ #

    def _open_settings(self) -> None:
        SettingsDialog(self, self._hotkey_manager, on_save=self._restart_hotkey)

    # ------------------------------------------------------------------ #
    #  Lifecycle
    # ------------------------------------------------------------------ #

    def _on_close(self) -> None:
        self._save_data()
        self._hotkey_manager.stop()
        self._edge_manager.stop()
        self.destroy()

    # ------------------------------------------------------------------ #
    #  Run
    # ------------------------------------------------------------------ #

    @classmethod
    def run(cls) -> None:
        app = cls()
        app.mainloop()
