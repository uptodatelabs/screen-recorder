"""Circular buffer for game highlight recording."""
import threading
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
            fps: Frames per second of the buffered footage.
            jpeg_quality: JPEG quality (0-100) used for in-memory frames.
        """
        if seconds < 1:
            raise ValueError("seconds must be >= 1")
        if fps < 1:
            raise ValueError("fps must be >= 1")

        self.capacity = int(seconds * fps)
        self.fps = fps
        self.jpeg_quality = jpeg_quality
        self.buffer: deque = deque(maxlen=self.capacity)
        self._is_recording = False
        self._lock = threading.Lock()

    def add_frame(self, frame: np.ndarray) -> None:
        """Encode and append a frame to the buffer (RGB ndarray)."""
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
                self.buffer.append(encoded)

    def get_frames(self) -> list:
        """Decode and return all buffered frames as BGR ndarrays."""
        with self._lock:
            encoded_frames = list(self.buffer)
        return [cv2.imdecode(enc, cv2.IMREAD_COLOR) for enc in encoded_frames]

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