"""Circular buffer for game highlight recording."""
import asyncio
from collections import deque
from typing import Optional, Callable
import numpy as np


class HighlightBuffer:
    """
    Circular buffer that stores recent screen captures.
    
    When the user triggers "save highlight", 
    the last N seconds of captured frames are saved as a video clip.
    """
    
    def __init__(
        self, 
        capacity_frames: int = 300,  # 5 minutes at 60fps
        fps: int = 60,
        region: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        Initialize the highlight buffer.
        
        Args:
            capacity_frames: Number of frames to buffer
            fps: Frames per second for the recording
            region: Optional (x, y, width, height) to capture specific area
        """
        self.capacity = capacity_frames
        self.fps = fps
        self.region = region
        self.buffer = deque(maxlen=capacity_frames)
        self._is_recording = False
        self._callback: Optional[Callable] = None
    
    def add_frame(self, frame: np.ndarray) -> None:
        """Add a frame to the buffer."""
        if self._is_recording:
            self.buffer.append(frame.copy())
    
    def set_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Set callback to call when saving highlight."""
        self._callback = callback
    
    def trigger_save(self) -> None:
        """Trigger saving the buffered highlight."""
        if not self.buffer:
            return
        
        # Convert buffer to video clip
        # This is a simplified version - actual video writing would use ffmpeg
        if self._callback:
            # Return the buffered frames for video encoding
            # In a real implementation, this would be written to a video file
            frames = list(self.buffer)
            self._callback(frames)
    
    def start_recording(self) -> None:
        """Start buffering frames."""
        self._is_recording = True
        self.buffer.clear()
    
    def stop_recording(self) -> None:
        """Stop buffering frames."""
        self._is_recording = False