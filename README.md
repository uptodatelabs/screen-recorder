# Game Recorder

A screen recorder specialized for gamers, focused on capturing highlight moments.

## Features

- **Buffer-based highlight saving**: Automatically saves the last 5 minutes of gameplay when you press a hotkey
- **Game process detection**: Automatically detects running games
- **Customizable hotkeys**: Configure your own shortcuts
- **Hardware-accelerated encoding**: Support for NVIDIA NVENC for minimal performance impact
- **Simple UI**: Minimal overlay that doesn't interfere with gameplay

## Installation

```bash
# Clone the repository
git clone https://github.com/uptodatelabs/screen-recorder.git
cd screen-recorder

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the recorder
python -m screen_recorder.src.main

# Or run directly
python main.py
```

### Basic Workflow

1. Launch the recorder
2. Start your game
3. Press **F12** (default hotkey) to save the last 5 minutes of gameplay
4. Find your recorded clip in the `clips/` directory

## Configuration

You can customize the hotkey and buffer time by running with arguments:

```bash
python main.py --hotkey "<f12>" --buffer-time 300 --fps 60
```

## Supported Games

The recorder automatically detects popular games including:
- Valorant
- League of Legends
- Counter-Strike 2
- Dota 2
- Overwatch
- Fortnite
- Apex Legends
- Minecraft

## Development

```bash
# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.