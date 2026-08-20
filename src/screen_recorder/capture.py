"""Screen capture module for game recording."""
import mss
from mss import mss as MSS
import numpy as np
from typing import Optional, Tuple


class ScreenCapture:
    """Captures screen regions using mss library."""
    
    def __init__(self, monitor_index: int = 1):
        """
        Initialize screen capture.
        
        Args:
            monitor_index: Which monitor to capture (1=primary, etc.)
        """
        self.sct = MSS()
        self.monitor_index = monitor_index
        self._setup_monitor()
    
    def _setup_monitor(self):
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
        
        if region:
            x, y, w, h = region
            img_rgb = img_rgb[y:y+h, x:x+w]
        
        return img_rgb
    
    def get_monitor(self) -> Tuple[int, int, int, int]:
        """Return monitor dimensions as (left, top, width, height)."""
        return (self.monitor["left"], self.monitor["top"], 
                self.monitor["width"], self.monitor["height"])