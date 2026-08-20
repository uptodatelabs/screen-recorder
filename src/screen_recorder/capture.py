"""Screen capture module for game recording."""
from typing import Optional, Tuple

import mss
import numpy as np

from .cursor import draw_cursor


class ScreenCapture:
    """Captures screen regions using mss library."""

    def __init__(self, monitor_index: int = 1, capture_cursor: bool = True):
        """
        Initialize screen capture.

        Args:
            monitor_index: Which monitor to capture (1=primary, etc.)
            capture_cursor: Whether to overlay the mouse cursor on frames.
        """
        self.sct = mss.mss()
        self.monitor_index = monitor_index
        self.capture_cursor = capture_cursor
        self._setup_monitor()

    def _setup_monitor(self) -> None:
        """Set up the monitor dimensions."""
        monitors = self.sct.monitors
        if self.monitor_index < len(monitors):
            self.monitor = monitors[self.monitor_index]
        else:
            self.monitor = monitors[0]  # fallback to primary

    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Capture screen region as numpy array.

        Args:
            region: (x, y, width, height) tuple. If None, captures full monitor.

        Returns:
            numpy array with RGB pixel data
        """
        # mss returns BGRA, convert to RGB
        img = np.array(self.sct.grab(self.monitor))
        img_rgb = img[:, :, :3][:, :, ::-1]  # BGRA to RGB

        # mss does not capture the cursor; overlay it manually
        if self.capture_cursor:
            draw_cursor(
                img_rgb,
                origin_left=self.monitor["left"],
                origin_top=self.monitor["top"],
            )

        if region:
            x, y, w, h = region
            img_rgb = img_rgb[y : y + h, x : x + w]

        return img_rgb

    def get_monitor(self) -> Tuple[int, int, int, int]:
        """Return monitor dimensions as (left, top, width, height)."""
        return (
            self.monitor["left"],
            self.monitor["top"],
            self.monitor["width"],
            self.monitor["height"],
        )