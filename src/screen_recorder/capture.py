"""Screen capture module for game recording."""
import ctypes
import sys
from typing import Optional, Tuple

import cv2
import mss
import numpy as np

from .cursor import draw_cursor


def _set_dpi_aware() -> None:
    """Make the process DPI-aware so screen metrics and cursor
    coordinates are in physical pixels on scaled displays."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class ScreenCapture:
    """Captures screen frames.

    Uses the DXGI Desktop Duplication API (via dxcam) when available for
    much higher frame rates (monitor refresh rate on animated screens),
    and falls back to mss (GDI BitBlt) otherwise.
    """

    def __init__(
        self,
        monitor_index: int = 1,
        capture_cursor: bool = True,
        scale: float = 1.0,
    ):
        """
        Initialize screen capture.

        Args:
            monitor_index: Which monitor to capture (1=primary, etc.)
            capture_cursor: Whether to overlay the mouse cursor on frames.
            scale: Frame scale factor (0.1-1.0). Lower values capture a
                smaller frame, which is faster.
        """
        _set_dpi_aware()
        if not 0.1 <= scale <= 1.0:
            raise ValueError("scale must be in [0.1, 1.0]")
        self.monitor_index = monitor_index
        self.capture_cursor = capture_cursor
        self.scale = scale
        self._backend = "mss"
        self.sct: Optional[mss.MSS] = None
        self._dxcam = None
        self.monitor = None
        if self._init_dxcam():
            self._backend = "dxcam"
        else:
            self.sct = mss.mss()
            self._setup_monitor()

    def _init_dxcam(self) -> bool:
        """Try to initialize the DXGI capture backend. Returns True on success."""
        try:
            import dxcam

            cam = dxcam.create(
                output_idx=self.monitor_index - 1, output_color="RGB"
            )
            if cam is None:
                return False
            # video_mode=True re-emits the last frame when the desktop does
            # not change; otherwise no frames are delivered on static screens
            # and saved clips would only cover the brief moments the screen
            # actually changed.
            cam.start(target_fps=0, video_mode=True)
            self._dxcam = cam
            # DXGI always captures the full physical display
            self.monitor = {
                "left": 0,
                "top": 0,
                "width": cam.width,
                "height": cam.height,
            }
            return True
        except Exception:
            self._dxcam = None
            return False

    def _setup_monitor(self) -> None:
        """Set up the monitor dimensions for the mss backend."""
        monitors = self.sct.monitors
        if self.monitor_index < len(monitors):
            self.monitor = monitors[self.monitor_index]
        else:
            self.monitor = monitors[0]  # fallback to primary

    def capture(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Capture screen region as numpy array.

        Args:
            region: (x, y, width, height) tuple. If None, captures full monitor.

        Returns:
            numpy array with RGB pixel data, or None if no frame is ready yet
        """
        if self._backend == "dxcam":
            frame = self._dxcam.get_latest_frame()
            if frame is None:
                return None
            img_rgb = np.array(frame)  # copy out of dxcam's internal buffer
        else:
            # mss returns BGRA, convert to RGB
            img = np.array(self.sct.grab(self.monitor))
            img_rgb = img[:, :, :3][:, :, ::-1]  # BGRA to RGB

        # neither backend captures the cursor; overlay it manually
        if self.capture_cursor:
            draw_cursor(
                img_rgb,
                origin_left=self.monitor["left"],
                origin_top=self.monitor["top"],
            )

        # Optional downscale for higher capture fps
        if self.scale < 1.0:
            new_w = max(1, int(self.monitor["width"] * self.scale))
            new_h = max(1, int(self.monitor["height"] * self.scale))
            img_rgb = cv2.resize(
                img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA
            )

        if region:
            x, y, w, h = region
            img_rgb = img_rgb[y : y + h, x : x + w]

        return img_rgb

    def close(self) -> None:
        """Release the capture backend resources."""
        if self._dxcam is not None:
            try:
                self._dxcam.stop()
                self._dxcam.release()
            except Exception:
                pass
            self._dxcam = None

    def get_monitor(self) -> Tuple[int, int, int, int]:
        """Return monitor dimensions as (left, top, width, height)."""
        return (
            self.monitor["left"],
            self.monitor["top"],
            self.monitor["width"],
            self.monitor["height"],
        )