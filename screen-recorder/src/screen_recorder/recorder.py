"""Main recorder module that ties together capture, buffer, and hotkeys."""
import asyncio
import time
from typing import Optional
import numpy as np

from .capture import ScreenCapture
from .buffer import HighlightBuffer
from .hotkey import HotkeyManager


class GameRecorder:
    """Main recorder class for game highlights."""
    
    def __init__(self, 
                 buffer_capacity: int = 300,  # 5 min at 60fps
                 fps: int = 60,
                 hotkey: str = '<f12>'):
        """
        Initialize the game recorder.
        
        Args:
            buffer_capacity: Number of frames to buffer (default: 300 = 5 min at 60fps)
            fps: Frames per second for recording
            hotkey: Hotkey to trigger highlight save
        """
        self.hotkey = hotkey
        self.capture = ScreenCapture()
        self.buffer = HighlightBuffer(capacity_frames=buffer_capacity, fps=fps)
        self.hotkey_mgr = HotkeyManager()
        self.fps = fps
        self.buffer_capacity = buffer_capacity
        self.is_recording = False
        self.save_callback: Optional[callable] = None
    
    def set_save_callback(self, callback: callable) -> None:
        """Set callback function when highlight is saved."""
        self.save_callback = callback
        self.buffer.set_callback(callback)
    
    def start(self) -> None:
        """Start the recorder: begin buffering and register hotkey."""
        self.is_recording = True
        self.buffer.start_recording()
        
        # Register hotkey
        self.hotkey_mgr.register(self.hotkey, self._on_hotkey_press)
        self.hotkey_mgr.start_listening()
    
    def stop(self) -> None:
        """Stop the recorder."""
        self.is_recording = False
        self.buffer.stop_recording()
        self.hotkey_mgr.stop_listening()
    
    def _on_hotkey_press(self) -> None:
        """Handle hotkey press: save the last N minutes of recording."""
        self.buffer.trigger_save()
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame. Call while recording."""
        if not self.is_recording:
            return None
        return self.capture.capture()
    
    def get_status(self) -> dict:
        """Get current recorder status."""
        return {
            "is_recording": self.is_recording,
            "buffer_size": len(self.buffer.buffer),
            "buffer_capacity": self.buffer_capacity,
            "fps": self.fps
        }