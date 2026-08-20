"""Circular buffer for game highlight recording."""
import threading
import time
from collections import deque

import cv2
import numpy as np


class HighlightBuffer:
    """
    Circular buffer that stores recent screen captures as JPEG frames.

    When the user triggers "save highlight", the buffered frames are
    decoded and written to a video file.

    Frames are stored JPEG-compressed in memory to keep the memory
    footprint reasonable (a raw 1080p RGB frame is ~6 MB, a JPEG is
    typically 100-300 KB).

    Each entry records a capture timestamp, so the real-world duration
    of the buffered footage can be computed regardless of the actual
    frame rate the machine can sustain. The saved clip is written at
    the measured fps, so "the last N seconds" is saved faithfully even
    on slower hardware.

    All deque access is protected by a lock because frames are added
    by the capture loop thread while the hotkey listener thread reads
    them when saving a highlight.
    """

    def __init__(
        self,
        seconds: int = 30,
        fps: int = 30,
        jpeg_quality: int = 85,
    ):
        """
        Initialize the highlight buffer.

        Args:
            seconds: Number of seconds of footage to keep in memory.
            fps: Nominal capture frame rate; used to size the buffer.
            jpeg_quality: JPEG quality (0-100) used for in-memory frames.
        """
        if seconds < 1:
            raise ValueError("seconds must be >= 1")
        if fps < 1:
            raise ValueError("fps must be >= 1")

        self.capacity = int(seconds * fps)
        self.nominal_fps = fps
        self.seconds = seconds
        self.jpeg_quality = jpeg_quality
        self.buffer: deque = deque(maxlen=self.capacity)
        self._is_recording = False
        self._lock = threading.Lock()

    def add_frame(self, frame: np.ndarray, timestamp: float = None) -> None:
        """
        Encode and append a frame to the buffer (RGB ndarray).

        Args:
            frame: RGB frame to buffer.
            timestamp: Monotonic capture time; defaults to now.
        """
        if frame is None:
            return
        ok, encoded = cv2.imencode(
            ".jpg",
            cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
            [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
        )
        if not ok:
            return
        with self._lock:
            if self._is_recording:
                self.buffer.append((timestamp or time.monotonic(), encoded))

    def get_frames(self) -> list:
        """Decode and return all buffered frames as BGR ndarrays."""
        with self._lock:
            encoded_frames = [enc for _, enc in self.buffer]
        return [cv2.imdecode(enc, cv2.IMREAD_COLOR) for enc in encoded_frames]

    def snapshot(self) -> list:
        """Return the buffered JPEG frames as a list of encoded arrays.

        The returned list is independent of the buffer, so it stays valid
        even as new frames are appended and old ones dropped.
        """
        with self._lock:
            return [enc for _, enc in self.buffer]

    def duration(self) -> float:
        """
        Return the real-world duration (seconds) of the buffered footage.

        Falls back to frame_count / nominal_fps when fewer than 2 frames
        are buffered.
        """
        with self._lock:
            if len(self.buffer) < 2:
                return len(self.buffer) / self.nominal_fps if len(self.buffer) else 0.0
            first_ts = self.buffer[0][0]
            last_ts = self.buffer[-1][0]
        return max(0.0, last_ts - first_ts)

    def frame_count(self) -> int:
        """Return the number of frames currently buffered."""
        with self._lock:
            return len(self.buffer)

    def clear(self) -> None:
        """Clear all buffered frames."""
        with self._lock:
            self.buffer.clear()

    def start_recording(self) -> None:
        """Start buffering frames."""
        with self._lock:
            self._is_recording = True
            self.buffer.clear()

    def stop_recording(self) -> None:
        """Stop buffering frames."""
        with self._lock:
            self._is_recording = False