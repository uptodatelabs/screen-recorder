"""Hotkey handling module for global shortcuts."""
import threading
from pynput import keyboard
from typing import Callable, Dict, Set


class HotkeyManager:
    """Manages global hotkey registration and handling."""
    
    def __init__(self):
        """Initialize hotkey manager."""
        self._handlers: Dict[str, Callable] = {}
        self._listener: Optional[keyboard.GlobalHotKeys] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def register(self, hotkey: str, callback: Callable) -> None:
        """
        Register a hotkey with a callback.
        
        Args:
            hotkey: String representation of hotkey (e.g., '<f12>', '<ctrl>+<alt>+<shift>')
            callback: Function to call when hotkey is pressed
        """
        self._handlers[hotkey] = callback
    
    def start_listening(self) -> None:
        """Start listening for hotkeys in a separate thread."""
        if self._running:
            return
        
        def on_press(key):
            try:
                # Build hotkey string from pynput key
                key_str = self._key_to_string(key)
                if key_str in self._handlers:
                    self._handlers[key_str]()
            except Exception:
                pass
        
        def on_release(key):
            # Stop listener on ESC press
            if key == keyboard.Key.esc:
                return False
        
        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self._running = True
        self._thread = threading.Thread(target=self._listener.start, daemon=True)
        self._thread.start()
    
    def stop_listening(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        if self._listener:
            self._listener.stop()
    
    def _key_to_string(self, key) -> str:
        """Convert pynput key to string representation."""
        try:
            return key.char
        except AttributeError:
            key_name = str(key).replace('Key.', '<').replace('>', '>')
            return key_name.lower()
    
    def get_registered_hotkeys(self) -> Set[str]:
        """Get set of registered hotkey strings."""
        return set(self._handlers.keys())