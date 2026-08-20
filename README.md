# Game Recorder

A screen recorder specialized for gamers, focused on capturing highlight moments.

## Features

- **Buffer-based highlight saving**: Keep the last N seconds of gameplay in memory and save it as an MP4 clip with a single hotkey press
- **Game process detection**: Automatically detects running games
- **Customizable hotkeys**: Configure your own shortcuts (e.g. `f12`, `ctrl+shift+f12`)
- **High performance capture**: DXGI Desktop Duplication (via dxcam) captures at monitor refresh rate on animated screens, with a threaded encoder so grabs and encodes overlap
- **Mouse cursor overlay**: The cursor is drawn onto each frame (screen capture APIs don't include it)
- **Low performance impact**: JPEG-compressed in-memory buffering keeps memory usage low
- **CLI-first**: Simple, scriptable command line interface

## Requirements

- Windows (screen capture is currently tested on Windows)
- Python 3.10+

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
# Run the recorder (from the repository root)
python src/main.py
```

### Basic Workflow

1. Launch the recorder
2. Play your game
3. Press **F12** (default hotkey) to save the last 30 seconds of gameplay
4. Find your clip in the `clips/` directory (e.g. `clips/highlight_20260820_184421.mp4`)
5. Press **Ctrl+C** to stop the recorder

## Configuration

```bash
# Custom hotkey, buffer time, frame rate, and output directory
python src/main.py --hotkey "ctrl+shift+f12" --buffer-time 60 --fps 30 --output my_clips
```

| Option          | Description                                          | Default |
|-----------------|------------------------------------------------------|---------|
| `--hotkey`      | Hotkey that saves the highlight clip                 | `f12`   |
| `--buffer-time` | Seconds of gameplay kept in the buffer               | `30`    |
| `--fps`         | Capture frame rate (10-60 recommended)               | `30`    |
| `--output`      | Directory where clips are saved                      | `clips` |
| `--no-cursor`   | Do not overlay the mouse cursor on frames            | off     |
| `--scale`       | Frame scale factor, e.g. 0.5 = half resolution       | `1.0`   |

> **Note on frame rate**: Capture uses the DXGI Desktop Duplication API by
> default (falling back to GDI BitBlt via mss on unsupported systems). On
> animated screens (games), frames are delivered at your monitor's refresh
> rate; the encoder runs in a separate thread so screen grabs are never
> blocked by encoding. Clips are saved at the measured capture rate, so the
> video length always matches the real seconds of gameplay.
>
> **Note on fullscreen games**: DXGI cannot capture games running in
> *exclusive* (fullscreen exclusive) mode — the saved clip would show the
> frozen desktop. Use *borderless windowed* or *windowed* mode in your game
> so the desktop surface stays visible to the capture API. Highlights are
> saved in a background thread, so the hotkey stays responsive while the
> clip is being encoded.

## Supported Games

The recorder can auto-detect popular games (list shown when the game is running):
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

# Run tests with coverage
pytest --cov=src
```

## Project Structure

```
screen-recorder/
├── src/
│   ├── main.py                 # CLI entry point
│   └── screen_recorder/
│       ├── capture.py          # Screen capture (dxcam DXGI + mss fallback)
│       ├── buffer.py           # Circular highlight buffer (JPEG)
│       ├── hotkey.py           # Global hotkey handling (pynput)
│       ├── cursor.py           # Mouse cursor capture + overlay (GDI)
│       ├── game_detector.py    # Game process detection (psutil)
│       └── recorder.py         # Main recorder orchestrator
├── tests/
│   └── test_screen_recorder.py # Unit tests
├── clips/                      # Saved highlight clips (created at runtime)
└── requirements.txt
```

## Roadmap

- [x] Buffer-based highlight saving (MVP)
- [x] Global hotkey support
- [x] High-performance capture (DXGI Desktop Duplication)
- [ ] Hardware-accelerated encoding (NVENC / AMF / QSV)
- [ ] Audio recording (system + microphone mixing)
- [ ] Game-specific profiles
- [ ] Clip management UI
- [ ] Direct sharing (Twitch / YouTube / Discord)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

# 게임 레코더

게이머를 위한 화면 캡처 프로그램입니다. 게임 플레이의 하이라이트 순간을 놓치지 않고 저장하는 데 중점을 둡니다.

## 기능

- **버퍼 기반 하이라이트 저장**: 지난 N초의 게임 화면을 메모리에 보관했다가 핫키 한 번으로 MP4 클립으로 저장
- **게임 프로세스 자동 감지**: 실행 중인 게임을 자동으로 감지
- **사용자 정의 핫키**: 단축키 직접 설정 (예: `f12`, `ctrl+shift+f12`)
- **고성능 캡처**: DXGI 데스크톱 중복(DXGI Desktop Duplication, dxcam)으로 화면이 움직일 때 모니터 주사율만큼 캡처, 스레드 인코더로 캡처와 인코딩을 동시 처리
- **마우스 커서 오버레이**: 캡처 API에 포함되지 않는 커서를 각 프레임에 직접 그림
- **낮은 성능 영향**: JPEG 압축 메모리 버퍼링으로 메모리 사용량 최소화
- **CLI 우선**: 간단하고 스크립트로 자동화 가능한 커맨드라인 인터페이스

## 요구 사항

- Windows (현재 Windows에서 테스트됨)
- Python 3.10 이상

## 설치

```bash
# 저장소 클론
git clone https://github.com/uptodatelabs/screen-recorder.git
cd screen-recorder

# 종속성 설치
pip install -r requirements.txt
```

## 사용법

```bash
# 레코더 실행 (저장소 루트에서)
python src/main.py
```

### 기본 사용 흐름

1. 레코더를 실행합니다
2. 게임을 플레이합니다
3. 기본 핫키 **F12**를 눌러 지난 30초의 게임 플레이를 저장합니다
4. `clips/` 디렉토리에서 클립을 확인합니다 (예: `clips/highlight_20260820_184421.mp4`)
5. **Ctrl+C**를 눌러 레코더를 종료합니다

## 설정

```bash
# 핫키, 버퍼 시간, 프레임 레이트, 출력 폴더 변경
python src/main.py --hotkey "ctrl+shift+f12" --buffer-time 60 --fps 30 --output my_clips
```

| 옵션            | 설명                                          | 기본값  |
|-----------------|-----------------------------------------------|---------|
| `--hotkey`      | 하이라이트 클립을 저장하는 단축키             | `f12`   |
| `--buffer-time` | 버퍼에 보관할 게임 플레이 시간(초)            | `30`    |
| `--fps`         | 캡처 프레임 레이트 (10-60 권장)               | `30`    |
| `--output`      | 클립이 저장되는 폴더                          | `clips` |
| `--no-cursor`   | 프레임에 마우스 커서를 그리지 않음            | off     |
| `--scale`       | 프레임 배율 (예: 0.5 = 절반 해상도)           | `1.0`   |

> **프레임 레이트 참고**: 캡처는 기본적으로 DXGI 데스크톱 중복 API를 사용합니다
> (지원되지 않는 시스템에서는 mss/GDI로 자동 대체). 게임처럼 화면이 계속
> 움직이면 모니터 주사율만큼 프레임이 전달되며, 인코더가 별도 스레드에서
> 실행되어 캡처가 인코딩에 막히지 않습니다. 클립은 측정된 캡처 속도로 저장되어
> 영상 길이가 항상 실제 게임 플레이 시간과 일치합니다.
>
> **전체화면 게임 참고**: DXGI는 *독점* 전체화면(전체 화면 전용) 모드의
> 게임을 캡처할 수 없습니다 — 저장된 클립에는 멈춘 데스크톱이 보일 수
> 있습니다. 게임을 *테두리 없는 창 모드* 또는 *창 모드*로 실행하면 캡처
> API에 데스크톱 화면이 계속 노출됩니다. 하이라이트 저장은 백그라운드
> 스레드에서 진행되므로 인코딩 중에도 핫키가 즉시 응답합니다.

## 지원 게임

인기 게임을 자동 감지할 수 있습니다 (게임 실행 시 목록 확인 가능):
- 발로란트
- 리그 오브 레전드
- 카운터스트라이크 2
- 도타 2
- 오버워치
- 포트나이트
- 에이펙스 레전드
- 마인크래프트

## 개발

```bash
# 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src
```

## 프로젝트 구조

```
screen-recorder/
├── src/
│   ├── main.py                 # CLI 진입점
│   └── screen_recorder/
│       ├── capture.py          # 화면 캡처 (dxcam DXGI + mss 대체)
│       ├── buffer.py           # 순환 하이라이트 버퍼 (JPEG)
│       ├── hotkey.py           # 전역 단축키 처리 (pynput)
│       ├── cursor.py           # 마우스 커서 캡처 + 오버레이 (GDI)
│       ├── game_detector.py    # 게임 프로세스 감지 (psutil)
│       └── recorder.py         # 메인 레코더 오케스트레이터
├── tests/
│   └── test_screen_recorder.py # 단위 테스트
├── clips/                      # 저장된 하이라이트 클립 (실행 시 생성)
└── requirements.txt
```

## 로드맵

- [x] 버퍼 기반 하이라이트 저장 (MVP)
- [x] 전역 단축키 지원
- [x] 고성능 캡처 (DXGI 데스크톱 중복)
- [ ] 하드웨어 가속 인코딩 (NVENC / AMF / QSV)
- [ ] 오디오 녹음 (시스템 + 마이크 믹싱)
- [ ] 게임별 프로파일
- [ ] 클립 관리 UI
- [ ] 직접 공유 (트위치 / 유튜브 / 디스코드)

## 라이선스

본 프로젝트는 MIT 라이선스하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.