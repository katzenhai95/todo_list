"""Auto-hide / auto-show when docked to screen edge (left / right only)."""

from __future__ import annotations

import ctypes
import tkinter as tk
from enum import Enum, auto


class Edge(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class EdgeManager:
    """Manages auto-hide behaviour when window is docked to left or right screen edge.

    Behaviour:
    - When the user drags the window near the left/right screen edge and
      stops moving, it snaps flush to that edge.
    - When the mouse leaves the window, it slides off-screen after a short
      delay, leaving a 3 px handle visible.
    - When the mouse touches the handle, the window slides back into view.
    - Top and bottom edges are ignored.
    """

    ANIMATION_STEPS = 8        # how many frames per slide
    ANIMATION_INTERVAL = 10    # ms between frames
    HIDE_DELAY = 400           # ms before hiding starts
    HANDLE_WIDTH = 3           # px of the window left visible when hidden
    EDGE_THRESHOLD = 15        # px from screen edge to trigger docking

    def __init__(self, window: tk.Toplevel) -> None:
        self.window = window
        self._dock_edge: Edge = Edge.NONE

        # Original geometry (used to restore position)
        self._visible_x: int = 0
        self._visible_y: int = 0
        self._visible_width: int = 0
        self._visible_height: int = 0

        # State machine
        self._hidden = False
        self._animating = False
        self._hide_after_id: str | None = None

        # Polling
        self._poll_interval = 150  # ms
        self._poll_running = False
        self._mouse_was_inside = False

        # Snap-on-stop — driven by polling tick counter
        self._near_edge_count = 0  # consecutive ticks near edge with mouse inside
        self._snap_threshold = 2   # snap after this many consecutive edge-ticks (~300ms)

        self._start_polling()

    # ------------------------------------------------------------------ #
    #  Snap-to-edge (triggered by polling when window lingers near edge)
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #

    def start(self) -> None:
        self._start_polling()

    def stop(self) -> None:
        self._poll_running = False
        self._near_edge_count = 0
        if self._hide_after_id:
            self.window.after_cancel(self._hide_after_id)
            self._hide_after_id = None

    # ------------------------------------------------------------------ #
    #  Polling loop
    # ------------------------------------------------------------------ #

    def _start_polling(self) -> None:
        if self._poll_running:
            return
        self._poll_running = True
        self._poll()

    def _poll(self) -> None:
        if not self._poll_running:
            return
        try:
            self._tick()
        except Exception:
            pass
        self.window.after(self._poll_interval, self._poll)

    def _tick(self) -> None:
        """Check mouse position relative to window and screen edges."""
        if self._animating:
            return

        try:
            wx = self.window.winfo_x()
            wy = self.window.winfo_y()
            ww = self.window.winfo_width()
            wh = self.window.winfo_height()
        except tk.TclError:
            return

        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        mx, my = self._mouse_position()
        mouse_inside = (wx <= mx <= wx + ww) and (wy <= my <= wy + wh)

        if self._hidden:
            self._poll_hidden(mx, my, screen_w, screen_h)
            return

        edge = self._detect_edge(wx, wy, ww, wh, screen_w, screen_h)

        if edge != Edge.NONE:
            if mouse_inside:
                self._dock_edge = edge
                self._mouse_was_inside = True
                if self._hide_after_id:
                    self.window.after_cancel(self._hide_after_id)
                    self._hide_after_id = None

                # Snapping logic: if the window has been near this edge
                # for _snap_threshold consecutive ticks (~300ms), snap it flush.
                # already_snapped: skip re-snap ONLY when window is at the target
                # position. Use a bounded range — NOT a one-sided >= — so that
                # windows PAST the edge also trigger a corrective snap.
                already_snapped = (
                    (edge == Edge.LEFT and -3 <= wx <= 3)
                    or (edge == Edge.RIGHT and abs((wx + ww) - screen_w) <= 3)
                )
                if already_snapped:
                    self._near_edge_count = 0
                else:
                    self._near_edge_count += 1
                    if self._near_edge_count >= self._snap_threshold:
                        self._near_edge_count = 0
                        # Use current size; don't trust _visible_width (may be stale)
                        target_w = ww
                        target_h = wh
                        if edge == Edge.LEFT:
                            snap_x = 0
                        else:
                            snap_x = screen_w - target_w
                        self.window.geometry(
                            f"{target_w}x{target_h}+{snap_x}+{wy}"
                        )
                        self._visible_x = snap_x
                        self._visible_y = wy
                        self._visible_width = target_w
                        self._visible_height = target_h
                        self._dock_edge = edge
                        self._mouse_was_inside = True
            elif self._mouse_was_inside and self._dock_edge == edge:
                self._mouse_was_inside = False
                if not self._hide_after_id:
                    self._hide_after_id = self.window.after(
                        self.HIDE_DELAY, self._start_hide
                    )
        else:
            self._dock_edge = Edge.NONE
            self._mouse_was_inside = mouse_inside
            self._near_edge_count = 0
            if self._hide_after_id:
                self.window.after_cancel(self._hide_after_id)
                self._hide_after_id = None

    # ------------------------------------------------------------------ #
    #  Hidden state polling
    # ------------------------------------------------------------------ #

    def _poll_hidden(self, mx: int, my: int, screen_w: int, screen_h: int) -> None:
        """When hidden, check if mouse approaches the handle area."""
        wy = self.window.winfo_y()
        wh = self.window.winfo_height()

        if self._dock_edge == Edge.LEFT:
            trigger = (0 <= mx <= self.HANDLE_WIDTH + 5) and (wy <= my <= wy + wh)
        elif self._dock_edge == Edge.RIGHT:
            trigger = (screen_w - self.HANDLE_WIDTH - 5 <= mx <= screen_w) and (wy <= my <= wy + wh)
        else:
            trigger = False

        if trigger:
            self._start_show()

    # ------------------------------------------------------------------ #
    #  Edge detection  (left / right only)
    # ------------------------------------------------------------------ #

    def _detect_edge(
        self, wx: int, wy: int, ww: int, wh: int, screen_w: int, screen_h: int
    ) -> Edge:
        """Return which edge the window is docked to, or NONE.
        Only left and right edges are detected."""
        if wx <= self.EDGE_THRESHOLD:
            return Edge.LEFT
        if wx + ww >= screen_w - self.EDGE_THRESHOLD:
            return Edge.RIGHT
        return Edge.NONE

    # ------------------------------------------------------------------ #
    #  Hide / Show animation  (left / right only)
    # ------------------------------------------------------------------ #

    def _start_hide(self) -> None:
        self._hide_after_id = None
        if self._animating or self._hidden:
            return

        wx = self.window.winfo_x()
        wy = self.window.winfo_y()
        ww = self.window.winfo_width()
        wh = self.window.winfo_height()

        self._visible_x = wx
        self._visible_y = wy
        self._visible_width = ww
        self._visible_height = wh

        screen_w = self.window.winfo_screenwidth()

        if self._dock_edge == Edge.LEFT:
            target_x = -(ww - self.HANDLE_WIDTH)
            target_y = wy
        elif self._dock_edge == Edge.RIGHT:
            target_x = screen_w - self.HANDLE_WIDTH
            target_y = wy
        else:
            return

        self._animate_slide(wx, wy, target_x, target_y, hide=True)

    def _start_show(self) -> None:
        if self._animating or not self._hidden:
            return

        wx = self.window.winfo_x()
        wy = self.window.winfo_y()
        self._animate_slide(wx, wy, self._visible_x, self._visible_y, hide=False)

    def _animate_slide(
        self, from_x: int, from_y: int, to_x: int, to_y: int, *, hide: bool
    ) -> None:
        self._animating = True
        self._hidden = hide

        dx = (to_x - from_x) / self.ANIMATION_STEPS
        dy = (to_y - from_y) / self.ANIMATION_STEPS

        def step(i: int = 0) -> None:
            if i >= self.ANIMATION_STEPS:
                try:
                    self.window.geometry(f"+{to_x}+{to_y}")
                except tk.TclError:
                    pass
                self._animating = False
                return
            nx = int(from_x + dx * (i + 1))
            ny = int(from_y + dy * (i + 1))
            try:
                self.window.geometry(f"+{nx}+{ny}")
            except tk.TclError:
                self._animating = False
                return
            self.window.after(self.ANIMATION_INTERVAL, step, i + 1)

        step(0)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _mouse_position() -> tuple[int, int]:
        """Get global mouse position using Windows API."""
        try:
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        except Exception:
            return 0, 0
