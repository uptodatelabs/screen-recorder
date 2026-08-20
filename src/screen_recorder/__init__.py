__version__ = "0.1.0"

from .capture import ScreenCapture
from .buffer import HighlightBuffer
from .game_detector import GameDetector
from .hotkey import HotkeyManager
from .recorder import GameRecorder

__all__ = [
    "ScreenCapture",
    "HighlightBuffer",
    "GameDetector",
    "HotkeyManager",
    "GameRecorder",
    "__version__",
]