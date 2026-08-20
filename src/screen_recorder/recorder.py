"""Main recorder module that ties together capture, buffer, and hotkeys."""
import os
import queue
import sys
import threading
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
        capture_cursor: bool = True,
        scale: float = 1.0,
    ):
        """
        Initialize the game recorder.

        Args:
            buffer_seconds: How many seconds of footage to keep in the buffer.
            fps: Frames per second for capture and saved clips.
            hotkey: Global hotkey spec that saves the highlight.
            output_dir: Directory where highlight clips are written.
            capture_cursor: Whether to overlay the mouse cursor on frames.
            scale: Frame scale factor (0.1-1.0). Lower = higher fps,
                lower resolution.
        """
        self.hotkey = hotkey
        self.output_dir = output_dir
        self.fps = fps
        self.buffer_seconds = buffer_seconds
        self.capture_cursor = capture_cursor
        self.scale = scale
        self.capture = ScreenCapture(capture_cursor=capture_cursor, scale=scale)
        self.buffer = HighlightBuffer(seconds=buffer_seconds, fps=fps)
        self.hotkey_mgr = HotkeyManager()
        self.is_recording = False
        self.save_callback: Optional[Callable] = None
        self.save_started_callback: Optional[Callable] = None
        self.save_progress_callback: Optional[Callable] = None
        # Captured frames are handed to a worker thread for JPEG encoding so
        # the slow encode overlaps with the next screen grab.
        self._encode_queue: queue.Queue = queue.Queue(maxsize=2)
        self._encoder_thread: Optional[threading.Thread] = None
        # In-flight highlight saver threads, joined on stop() so clips are
        # never lost when the app exits right after a hotkey press.
        self._saver_threads: list = []

    def set_save_callback(self, callback: Callable) -> None:
        """Set a callback ``callback(clip_path, frame_count)`` for saved clips."""
        self.save_callback = callback

    def set_save_started_callback(self, callback: Callable) -> None:
        """Set a callback called the moment a highlight save is triggered."""
        self.save_started_callback = callback

    def set_save_progress_callback(self, callback: Callable) -> None:
        """Set a callback ``callback(frames_done, total_frames)`` for progress."""
        self.save_progress_callback = callback

    def start(self) -> None:
        """Start the recorder: begin buffering and register the hotkey."""
        self.is_recording = True
        self.buffer.start_recording()
        self._encoder_thread = threading.Thread(
            target=self._encode_worker, name="jpeg-encoder", daemon=True
        )
        self._encoder_thread.start()
        self.hotkey_mgr.register(self.hotkey, self._on_hotkey_press)
        self.hotkey_mgr.start_listening()

    def stop(self) -> None:
        """Stop the recorder."""
        self.is_recording = False
        self.buffer.stop_recording()
        self.hotkey_mgr.stop_listening()
        # Signal the encoder thread and wait for it to drain.
        if self._encoder_thread is not None:
            try:
                self._encode_queue.put_nowait((None, None))
            except queue.Full:
                pass
            self._encoder_thread.join(timeout=2.0)
            self._encoder_thread = None
        self.capture.close()
        # Wait for in-flight highlight saves so the last clip is not lost
        # when the app exits (saver threads are daemon threads).
        for t in self._saver_threads:
            if t.is_alive():
                t.join()

    def capture_frame(self) -> None:
        """Capture one frame and queue it for encoding into the buffer."""
        if not self.is_recording:
            return
        frame = self.capture.capture()
        if frame is None:
            return  # backend not ready yet, skip this tick
        self._encode_queue.put((frame, time.monotonic()))

    def _encode_worker(self) -> None:
        """Consume captured frames, JPEG-encode, and store into the buffer."""
        while True:
            try:
                frame, timestamp = self._encode_queue.get(timeout=0.2)
            except queue.Empty:
                if not self.is_recording:
                    return
                continue
            if frame is None:
                return
            self.buffer.add_frame(frame, timestamp)

    def _on_hotkey_press(self) -> None:
        """Handle hotkey press: save the buffered highlight as a video clip.

        The clip is written in a background thread so the hotkey returns
        immediately; encoding 30s of full-resolution frames takes tens of
        seconds of CPU time.
        """
        if self.buffer.frame_count() == 0:
            return
        encoded_frames = self.buffer.snapshot()
        if not encoded_frames:
            return
        if self.save_started_callback is not None:
            self.save_started_callback(len(encoded_frames), duration)
        duration = self.buffer.duration()
        # Play back the clip at the measured capture rate so its length
        # matches the real seconds of gameplay, even on slow hardware.
        if duration > 0.2:
            fps = max(1, round(len(encoded_frames) / duration))
        else:
            fps = self.fps
        saver = threading.Thread(
            target=self._save_clip_async,
            args=(encoded_frames, fps, duration),
            name="clip-saver",
            daemon=True,
        )
        self._saver_threads.append(saver)
        saver.start()

    def _save_clip_async(self, encoded_frames: list, fps: int, duration: float) -> None:
        """Decode buffered frames and write the highlight clip in the background.

        Frames are decoded and written one at a time so memory stays low
        even for large buffers (decoding everything at once would need
        tens of gigabytes for a full 30s buffer).
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            first = cv2.imdecode(encoded_frames[0], cv2.IMREAD_COLOR)
            height, width = first.shape[:2]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clip_path = os.path.join(
                self.output_dir, f"highlight_{timestamp}.mp4"
            )
            writer = cv2.VideoWriter(
                clip_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height),
            )
            if not writer.isOpened():
                raise RuntimeError(f"Could not open video writer for {clip_path}")
            try:
                writer.write(first)
                total = len(encoded_frames)
                for i, enc in enumerate(encoded_frames[1:], start=2):
                    writer.write(cv2.imdecode(enc, cv2.IMREAD_COLOR))
                    if (
                        self.save_progress_callback is not None
                        and i % 20 == 0
                    ):
                        self.save_progress_callback(i, total)
            finally:
                writer.release()
        except Exception as e:
            print(f"ERROR: failed to save highlight: {e}", file=sys.stderr)
            return
        if self.save_callback is not None:
            self.save_callback(clip_path, len(encoded_frames), duration, fps)

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