"""Circular buffer for game highlight recording."""
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

    def add_frame(self, frame: np.ndarray) -> None:
        """Encode and append a frame to the buffer (RGB ndarray)."""
        if not self._is_recording or frame is None:
            return
        ok, encoded = cv2.imencode(
            ".jpg",
            cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
            [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality],
        )
        if ok:
            self.buffer.append(encoded)

    def get_frames(self) -> list:
        """Decode and return all buffered frames as BGR ndarrays."""
        return [cv2.imdecode(enc, cv2.IMREAD_COLOR) for enc in self.buffer]

    def frame_count(self) -> int:
        """Return the number of frames currently buffered."""
        return len(self.buffer)

    def clear(self) -> None:
        """Clear all buffered frames."""
        self.buffer.clear()

    def start_recording(self) -> None:
        """Start buffering frames."""
        self._is_recording = True
        self.clear()

    def stop_recording(self) -> None:
        """Stop buffering frames."""
        self._is_recording = False