"""Tests for edge detection and multi-monitor support."""

from __future__ import annotations

import pytest

from edge import Edge, EdgeManager


class TestDetectEdgeSingleMonitor:
    """TC-F009: Edge detection on single 1920px monitor."""

    SCREEN_W = 1920

    @pytest.fixture(autouse=True)
    def _mock(self, monkeypatch) -> None:
        def fake(inst, wx, wy, ww, wh):
            return None
        monkeypatch.setattr(EdgeManager, "_get_monitor_bounds", fake)

    def _detect(self, wx: int, ww: int = 400) -> Edge:
        return EdgeManager._detect_edge(
            EdgeManager.__new__(EdgeManager), wx, 0, ww, 600, self.SCREEN_W, 1080,
        )

    def test_left_edge(self) -> None:
        assert self._detect(0) == Edge.LEFT

    def test_right_edge(self) -> None:
        assert self._detect(1520) == Edge.RIGHT

    def test_middle_no_edge(self) -> None:
        assert self._detect(500) == Edge.NONE

    def test_just_beyond_threshold(self) -> None:
        assert self._detect(16) == Edge.NONE
        assert self._detect(1504) == Edge.NONE


class TestDetectEdgeMultiMonitor:
    """TC-F009: Multi-monitor — two 1920px screens side by side."""

    SCREEN_W = 3840

    @pytest.fixture(autouse=True)
    def _mock(self, monkeypatch) -> None:
        def fake(inst, wx, wy, ww, wh):
            cx = wx + ww // 2
            return (0, 1920) if cx < 1920 else (1920, 3840)
        monkeypatch.setattr(EdgeManager, "_get_monitor_bounds", fake)

    def _detect(self, wx: int, ww: int = 400) -> Edge:
        return EdgeManager._detect_edge(
            EdgeManager.__new__(EdgeManager), wx, 0, ww, 600, self.SCREEN_W, 1080,
        )

    def test_left_monitor_right_edge(self) -> None:
        assert self._detect(1520) == Edge.RIGHT

    def test_right_monitor_left_edge(self) -> None:
        assert self._detect(1920) == Edge.LEFT

    def test_right_monitor_right_edge(self) -> None:
        assert self._detect(3440) == Edge.RIGHT

    def test_middle_of_left_monitor(self) -> None:
        assert self._detect(500) == Edge.NONE

    def test_middle_of_right_monitor(self) -> None:
        assert self._detect(2500) == Edge.NONE
