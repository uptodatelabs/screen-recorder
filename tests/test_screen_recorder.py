"""Unit tests for screen_recorder modules."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pytest

from screen_recorder.buffer import HighlightBuffer
from screen_recorder.hotkey import HotkeyManager
from screen_recorder.game_detector import GameDetector


def make_frame(value: int = 0, size: int = 64) -> np.ndarray:
    """Create a small solid-color RGB frame."""
    return np.full((size, size, 3), value, dtype=np.uint8)


class TestHighlightBuffer:
    def test_buffers_up_to_capacity(self):
        buffer = HighlightBuffer(seconds=2, fps=10)
        buffer.start_recording()
        for i in range(30):
            buffer.add_frame(make_frame(i))
        assert buffer.frame_count() == 20

    def test_discards_frames_when_not_recording(self):
        buffer = HighlightBuffer(seconds=2, fps=10)
        for i in range(10):
            buffer.add_frame(make_frame(i))
        assert buffer.frame_count() == 0

    def test_roundtrip_decode(self):
        buffer = HighlightBuffer(seconds=1, fps=10)
        buffer.start_recording()
        buffer.add_frame(make_frame(120))
        frames = buffer.get_frames()
        assert len(frames) == 1
        assert frames[0].shape == (64, 64, 3)

    def test_invalid_arguments(self):
        with pytest.raises(ValueError):
            HighlightBuffer(seconds=0, fps=10)
        with pytest.raises(ValueError):
            HighlightBuffer(seconds=10, fps=0)


class TestHotkeyManager:
    def test_parse_spec_styles(self):
        assert HotkeyManager._parse_spec("<f12>") == ("f12",)
        assert HotkeyManager._parse_spec("ctrl+shift+s") == ("ctrl", "s", "shift")
        assert HotkeyManager._parse_spec("  Ctrl + F9 ") == ("ctrl", "f9")

    def test_register_rejects_empty(self):
        manager = HotkeyManager()
        with pytest.raises(ValueError):
            manager.register("", lambda: None)

    def test_register_and_get(self):
        manager = HotkeyManager()
        manager.register("f12", lambda: None)
        manager.register("ctrl+shift+s", lambda: None)
        assert manager.get_registered_hotkeys() == {"f12", "ctrl+shift+s"}


class TestGameDetector:
    def test_returns_list_of_games(self):
        detector = GameDetector()
        games = detector.get_running_games()
        assert isinstance(games, list)

    def test_game_pid_returns_int_or_none(self):
        detector = GameDetector()
        pid = detector.get_game_pid("definitely_not_a_real_game_xyz")
        assert pid is None