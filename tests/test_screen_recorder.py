"""Unit tests for screen_recorder modules."""
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pytest

from screen_recorder.buffer import HighlightBuffer
from screen_recorder.hotkey import HotkeyManager
from screen_recorder.game_detector import GameDetector
from screen_recorder.cursor import _blend_into


def make_frame(value: int = 0, size: int = 64) -> np.ndarray:
    """Create a small solid-color RGB frame."""
    return np.full((size, size, 3), value, dtype=np.uint8)


class TestHighlightBuffer:
    def test_buffers_up_to_capacity(self):
        buffer = HighlightBuffer(seconds=2, fps=10)
        buffer.start_recording()
        for i in range(30):
            # 30 frames spread over 3 seconds; only the last 2s should stay
            buffer.add_frame(make_frame(i), timestamp=100.0 + i * 0.1)
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

    def test_duration_reflects_real_time(self):
        buffer = HighlightBuffer(seconds=5, fps=10)
        buffer.start_recording()
        base = 1000.0
        for i in range(10):
            buffer.add_frame(make_frame(i), timestamp=base + i * 0.5)
        assert buffer.frame_count() == 10
        assert buffer.duration() == pytest.approx(4.5, abs=0.01)

    def test_duration_empty_buffer(self):
        buffer = HighlightBuffer(seconds=5, fps=10)
        buffer.start_recording()
        assert buffer.duration() == 0.0

    def test_invalid_arguments(self):
        with pytest.raises(ValueError):
            HighlightBuffer(seconds=0, fps=10)
        with pytest.raises(ValueError):
            HighlightBuffer(seconds=10, fps=0)

    def test_concurrent_add_and_read(self):
        """Simulates the capture thread writing while the hotkey thread reads."""
        buffer = HighlightBuffer(seconds=2, fps=10)
        buffer.start_recording()
        stop = threading.Event()
        errors = []

        def producer():
            i = 0
            while not stop.is_set():
                buffer.add_frame(make_frame(i))
                i += 1

        def consumer():
            while not stop.is_set():
                try:
                    buffer.get_frames()
                    buffer.frame_count()
                except Exception as exc:  # pragma: no cover
                    errors.append(exc)

        threads = [
            threading.Thread(target=producer),
            threading.Thread(target=consumer),
            threading.Thread(target=consumer),
        ]
        for t in threads:
            t.start()
        stop.set()
        for t in threads:
            t.join()
        assert errors == []


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


class TestCursorBlend:
    def test_blend_draws_into_frame(self):
        frame = np.full((100, 100, 3), 12, dtype=np.uint8)
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        rgba[5:25, 5:25, :3] = 255
        rgba[5:25, 5:25, 3] = 255
        _blend_into(frame, rgba, 40, 40)
        colors = set(map(tuple, frame[40:70, 40:70].reshape(-1, 3)))
        assert (255, 255, 255) in colors
        assert (12, 12, 12) in colors

    def test_blend_clips_outside_frame(self):
        frame = np.full((50, 50, 3), 12, dtype=np.uint8)
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        rgba[:, :, 3] = 255
        rgba[:, :, :3] = 255
        _blend_into(frame, rgba, 100, 100)
        assert set(map(tuple, frame.reshape(-1, 3))) == {(12, 12, 12)}

    def test_blend_partial_overlap(self):
        frame = np.full((50, 50, 3), 12, dtype=np.uint8)
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        rgba[:, :, 3] = 255
        rgba[:, :, :3] = 255
        _blend_into(frame, rgba, 40, 40)
        assert (255, 255, 255) in set(map(tuple, frame.reshape(-1, 3)))

    def test_blend_premultiplied_source(self):
        """Windows cursor bitmaps are premultiplied; blending must not
        double-multiply alpha and wash out the cursor."""
        frame = np.full((100, 100, 3), 12, dtype=np.uint8)
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        # premultiplied: gray (128,128,128) with alpha 128
        rgba[5:25, 5:25, :3] = 128
        rgba[5:25, 5:25, 3] = 128
        _blend_into(frame, rgba, 40, 40)
        px = tuple(frame[45, 45])
        # with premultiplied formula: src + dst*(1-a) = 128 + 12*0.5 = 134
        # with (buggy) straight formula: src*a + dst*(1-a) = 64 + 6 = 70
        assert all(130 <= c <= 140 for c in px), f"unexpected pixel {px}"