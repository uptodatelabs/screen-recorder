# 게임 레코더

게이머를 위한 화면 캡처 프로그램에 특화된 프로젝트입니다. 주요 하이라이트 순간을 캡처하는 데 중점을 둡니다.

## 기능

- **버퍼 기반 하이라이트 저장**: 핫키를 누르면 마지막 5분간 게임 플레이를 자동 저장
- **게임 프로세스 자동 감지**: 실행 중인 게임을 자동으로 감지
- **사용자 정의 핫키**: 사용자 지정 단축키 설정 가능
- **하드웨어 가속 인코딩**: NVIDIA NVENC 지원으로 minimal 성능 영향
- **간단한 UI**: 게임 플레이에 방해가 되지 않는 최소 오버레이

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
# 레코더 실행
python -m screen_recorder.src.main

# 또는 직접 실행
python main.py
```

### 기본 워크플로우

1. 레코더를 실행합니다
2. 게임을 실행합니다
3. 기본 핫키 **F12**를 눌러 지난 5분의 게임 플레이를 저장합니다
4. 기록된 클립은 `clips/` 디렉토리에서 확인할 수 있습니다

## 설정

인수를 사용하여 핫키와 버퍼 시간을 사용자 정의할 수 있습니다:

```bash
python main.py --hotkey "<f12>" --buffer-time 300 --fps 60
```

## 지원 게임

자동 감지되는 인기 게임:
- 발로란트
- 리그 오브 레전드
- 카운터스트라이크 2
- 도타 2
- 오버워치
- 포트나이트
- 에픽 레전드
- 마인크래프트

## 개발

```bash
# 테스트 실행
pytest

# 코드 포맷팅
black src/

# 린트
flake8 src/
```

## 라이선스

본 프로젝트는 MIT 라이선스하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.