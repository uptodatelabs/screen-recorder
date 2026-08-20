"""Hotkey handling module for global shortcuts."""
import threading
from typing import Callable, Dict, Set, Tuple

from pynput import keyboard


class HotkeyManager:
    """
    Manages global hotkey registration and handling.

    Hotkey specifications use the form ``"ctrl+shift+f12"`` or
    ``"<f12>"`` style. Keys are matched by tracking which keys are
    currently held down, so combos work correctly.
    """

    def __init__(self):
        self._handlers: Dict[Tuple[str, ...], Callable] = {}
        self._pressed: Set[str] = set()
        self._listener = None
        self._thread: threading.Thread = None
        self._running = False

    @staticmethod
    def _tokenize_key(key) -> str:
        """Convert a pynput key object to a normalized string token."""
        if isinstance(key, keyboard.KeyCode) and key.char:
            return key.char.lower()
        name = getattr(key, "name", None)
        if name is None:
            name = str(key).replace("Key.", "")
        return name

    @staticmethod
    def _parse_spec(spec: str) -> Tuple[str, ...]:
        """
        Parse a hotkey spec string into a normalized tuple of tokens.

        Accepts ``"<f12>"`` and ``"ctrl+shift+s"`` styles.
        """
        cleaned = spec.lower().replace("<", "").replace(">", "").replace(" ", "")
        tokens = sorted(t for t in cleaned.split("+") if t)
        return tuple(tokens)

    def register(self, hotkey: str, callback: Callable) -> None:
        """
        Register a hotkey with a callback.

        Args:
            hotkey: String specification, e.g. ``"<f12>"`` or ``"ctrl+shift+s"``.
            callback: Function to call when the hotkey is triggered.
        """
        tokens = self._parse_spec(hotkey)
        if not tokens:
            raise ValueError(f"Invalid hotkey spec: {hotkey!r}")
        display = "+".join(hotkey.lower().replace("<", "").replace(">", "").replace(" ", "").split("+"))
        self._handlers[tokens] = (display, callback)

    def _on_press(self, key) -> None:
        self._pressed.add(self._tokenize_key(key))
        for tokens, (display, callback) in self._handlers.items():
            if set(tokens).issubset(self._pressed):
                callback()

    def _on_release(self, key) -> None:
        self._pressed.discard(self._tokenize_key(key))

    def start_listening(self) -> None:
        """Start listening for hotkeys in a separate thread."""
        if self._running:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._running = True
        self._thread = threading.Thread(target=self._listener.start, daemon=True)
        self._thread.start()

    def stop_listening(self) -> None:
        """Stop listening for hotkeys."""
        self._running = False
        if self._listener is not None:
            self._listener.stop()
        self._pressed.clear()

    def get_registered_hotkeys(self) -> Set[str]:
        """Return the registered hotkey specs."""
        return {display for display, _ in self._handlers.values()}