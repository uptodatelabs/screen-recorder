"""Main recorder module that ties together capture, buffer, and hotkeys."""
import os
import time
from datetime import datetime
from typing import Callable, Optional

import cv2

from .capture import ScreenCapture
from .buffer import HighlightBuffer
from .hotkey import HotkeyManager


class GameRecorder:
    """Main recorder class for game highlights."""

    def __init__(
        self,
        buffer_seconds: int = 30,
        fps: int = 30,
        hotkey: str = "f12",
        output_dir: str = "clips",
    ):
        """
        Initialize the game recorder.

        Args:
            buffer_seconds: How many seconds of footage to keep in the buffer.
            fps: Frames per second for capture and saved clips.
            hotkey: Global hotkey spec that saves the highlight.
            output_dir: Directory where highlight clips are written.
        """
        self.hotkey = hotkey
        self.output_dir = output_dir
        self.fps = fps
        self.buffer_seconds = buffer_seconds
        self.capture = ScreenCapture()
        self.buffer = HighlightBuffer(seconds=buffer_seconds, fps=fps)
        self.hotkey_mgr = HotkeyManager()
        self.is_recording = False
        self.save_callback: Optional[Callable] = None
        self._frame_interval = 1.0 / fps

    def set_save_callback(self, callback: Callable) -> None:
        """Set a callback ``callback(clip_path, frame_count)`` for saved clips."""
        self.save_callback = callback

    def start(self) -> None:
        """Start the recorder: begin buffering and register the hotkey."""
        self.is_recording = True
        self.buffer.start_recording()
        self.hotkey_mgr.register(self.hotkey, self._on_hotkey_press)
        self.hotkey_mgr.start_listening()

    def stop(self) -> None:
        """Stop the recorder."""
        self.is_recording = False
        self.buffer.stop_recording()
        self.hotkey_mgr.stop_listening()

    def capture_frame(self) -> None:
        """Capture one frame and feed it into the highlight buffer."""
        if not self.is_recording:
            return
        frame = self.capture.capture()
        self.buffer.add_frame(frame)

    def _on_hotkey_press(self) -> None:
        """Handle hotkey press: save the buffered highlight as a video clip."""
        if self.buffer.frame_count() == 0:
            return
        frames = self.buffer.get_frames()
        if not frames:
            return
        duration = self.buffer.duration()
        # Play back the clip at the measured capture rate so its length
        # matches the real seconds of gameplay, even on slow hardware.
        if duration > 0.2:
            fps = max(1, round(len(frames) / duration))
        else:
            fps = self.fps
        clip_path = self._write_clip(frames, fps)
        if self.save_callback is not None:
            self.save_callback(clip_path, len(frames), duration, fps)

    def _write_clip(self, frames: list, fps: int) -> str:
        """Write the given BGR frames to an MP4 file and return its path."""
        os.makedirs(self.output_dir, exist_ok=True)
        height, width = frames[0].shape[:2]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clip_path = os.path.join(self.output_dir, f"highlight_{timestamp}.mp4")

        writer = cv2.VideoWriter(
            clip_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not open video writer for {clip_path}")
        try:
            for frame in frames:
                writer.write(frame)
        finally:
            writer.release()
        return clip_path

    def get_status(self) -> dict:
        """Return the current recorder status."""
        return {
            "is_recording": self.is_recording,
            "buffer_frames": self.buffer.frame_count(),
            "buffer_capacity": self.buffer.capacity,
            "fps": self.fps,
            "buffer_seconds": self.buffer_seconds,
            "hotkey": self.hotkey,
            "output_dir": self.output_dir,
        }