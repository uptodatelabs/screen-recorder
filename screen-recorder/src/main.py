"""Main entry point for the Game Recorder application."""
import sys
import argparse
import os

# Add src directory to path so we can import screen_recorder package
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from screen_recorder.capture import ScreenCapture
from screen_recorder.buffer import HighlightBuffer
from screen_recorder.game_detector import GameDetector
from screen_recorder.hotkey import HotkeyManager
from screen_recorder.recorder import GameRecorder


def main():
    """Main function to run the game recorder."""
    parser = argparse.ArgumentParser(
        description="Game Recorder - Capture game highlights with a single hotkey"
    )
    parser.add_argument(
        "--hotkey", 
        default="<f12>", 
        help="Hotkey to save highlight (default: <f12>)"
    )
    parser.add_argument(
        "--buffer-time", 
        type=int, 
        default=300, 
        help="Buffer time in frames (default: 300 = 5 min at 60fps)"
    )
    parser.add_argument(
        "--fps", 
        type=int, 
        default=60, 
        help="Frames per second (default: 60)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Game Recorder - MVP Version")
    print("=" * 50)
    print(f"Hotkey: {args.hotkey}")
    print(f"Buffer time: {args.buffer_time} frames (~{args.buffer_time / args.fps:.1f} seconds)")
    print(f"FPS: {args.fps}")
    print("=" * 50)
    print("Starting recorder...")
    print(f"Press {args.hotkey} to save the last {args.buffer_time / args.fps:.1f} minutes of gameplay")
    print("Press ESC to exit")
    print()
    
    recorder = GameRecorder(
        buffer_capacity=args.buffer_time,
        fps=args.fps,
        hotkey=args.hotkey
    )
    
    # Set up save callback
    def on_save(frames):
        print(f"\n✓ Highlight saved! {len(frames)} frames captured")
        # In a real implementation, this would encode to video
        # and save to disk
    
    recorder.set_save_callback(on_save)
    
    # Start recorder
    recorder.start()
    
    # Main loop - capture frames
    try:
        while True:
            frame = recorder.capture_frame()
            if frame is not None:
                # Frame captured successfully (for stats display)
                pass
            import time
            time.sleep(1.0 / args.fps)
    except KeyboardInterrupt:
        print("\nStopping recorder...")
    finally:
        recorder.stop()
        print("Recorder stopped.")


if __name__ == "__main__":
    main()