"""Main entry point for the Game Recorder application."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from screen_recorder.recorder import GameRecorder


def main() -> None:
    """Run the game recorder CLI."""
    parser = argparse.ArgumentParser(
        description="Game Recorder - Capture game highlights with a single hotkey"
    )
    parser.add_argument(
        "--hotkey",
        default="f12",
        help="Hotkey to save highlight, e.g. 'f12' or 'ctrl+shift+f12' (default: f12)",
    )
    parser.add_argument(
        "--buffer-time",
        type=int,
        default=30,
        help="Seconds of footage kept in the buffer (default: 30)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Capture frames per second (default: 30)",
    )
    parser.add_argument(
        "--output",
        default="clips",
        help="Directory where highlight clips are saved (default: clips)",
    )
    parser.add_argument(
        "--no-cursor",
        action="store_true",
        help="Do not overlay the mouse cursor on captured frames",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Capture scale factor for higher fps (0.5 = half resolution, default: 1.0)",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Game Recorder - MVP Version")
    print("=" * 50)
    print(f"Hotkey       : {args.hotkey}")
    print(f"Buffer time  : {args.buffer_time} seconds")
    print(f"FPS          : {args.fps}")
    print(f"Output dir   : {args.output}")
    print(f"Cursor       : {'off' if args.no_cursor else 'on'}")
    print(f"Scale        : {args.scale:.0%}")
    print("=" * 50)
    print("Starting recorder...")
    print(f"Press {args.hotkey} to save the last {args.buffer_time} seconds of gameplay")
    print("Press Ctrl+C to exit")
    print()

    recorder = GameRecorder(
        buffer_seconds=args.buffer_time,
        fps=args.fps,
        hotkey=args.hotkey,
        output_dir=args.output,
        capture_cursor=not args.no_cursor,
        scale=args.scale,
    )

    def on_save_started(frame_count: int) -> None:
        print(f"\nSaving highlight ({frame_count} frames)...")

    def on_save_progress(done: int, total: int) -> None:
        print(f"  Saving highlight... {done}/{total} frames ({done * 100 // total}%)", end="\r", flush=True)

    def on_save(clip_path: str, frame_count: int, duration: float, fps: int) -> None:
        print(f"\nSaved highlight: {clip_path}")
        print(f"  {frame_count} frames, {duration:.1f}s of gameplay, {fps} fps")

    recorder.set_save_callback(on_save)
    recorder.set_save_started_callback(on_save_started)
    recorder.set_save_progress_callback(on_save_progress)
    recorder.start()

    try:
        # The encoder queue's backpressure paces capture automatically;
        # sleep would only stack on top of the grab time.
        while recorder.is_recording:
            recorder.capture_frame()
    except KeyboardInterrupt:
        print("\nStopping recorder...")
    finally:
        recorder.stop()
        print("Recorder stopped.")


if __name__ == "__main__":
    main()