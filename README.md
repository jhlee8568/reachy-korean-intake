---
title: Reachy Korean Intake
emoji: 🌿
colorFrom: green
colorTo: gray
sdk: static
pinned: false
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# 리치 미니 한국어 문진

Reachy Mini Wireless용 독립 앱입니다. 세 가지 문진 질문에 한국어로 답하고, 문진이 끝나면 가벼운 스몰토크를 나눕니다. 기존 Conversation 앱과 다른 패키지로 설치됩니다.

## 기능

- 한국어 화면: 문진 시작, 다시 시작, 대화 종료, 질문 진행과 연결 상태.
- 세 질문: 불편한 곳, 시작 시점, 불편한 정도(0~10).
- 질문 순서·점수 확인·재질문 횟수·스몰토크 전환은 코드로 관리합니다.
- 한국어 Whisper 인식과 기존 Hugging Face 음성 대화 기능(Sohee)을 사용합니다. 별도 API 키가 필요하지 않습니다.
- 음성 응답은 언어 모델이 생성하므로 지정한 문장의 정확한 재생은 보장하지 않습니다.

문진 연습·시연용입니다. 의료 진단이나 치료를 제공하지 않습니다.

## 구성

로봇 마이크 → SSH 터널 → Mac Whisper → 한국어 텍스트 → Hugging Face 대화 서비스 → 로봇 스피커.

Mac 도우미가 켜져 있어야 합니다. 로봇과 Mac은 같은 네트워크에 연결하고, 음성 대화 서비스에 접근할 수 있는 인터넷이 필요합니다. 로봇이 말하는 동안은 입력을 받지 않습니다. 도우미가 끊겨도 영어 인식기로 전환하지 않습니다.

이 앱은 원음이나 문진 답변을 파일로 저장하지 않습니다. 답변 텍스트는 외부 대화 서비스로 전달됩니다. 현재 세션의 답변은 메모리에 유지되며 종료/다시 시작 시 앱의 답변 목록을 지웁니다. 원격 서비스의 대화 내역을 삭제하는 기능은 아닙니다.

## 설치

Python 3.12를 권장합니다. 로봇에는 일반 앱 패키지를 설치합니다.

```sh
/venvs/apps_venv/bin/python -m pip install /path/to/reachy_korean_intake-0.1.0-py3-none-any.whl
```

Mac에는 별도 가상환경에서 도우미를 설치합니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '/path/to/reachy_korean_intake-0.1.0-py3-none-any.whl[companion]'
.venv/bin/reachy-korean-companion
```

첫 실행은 Whisper small 모델을 다운로드합니다. 이후 캐시를 사용합니다. 기존 모델 폴더를 사용하려면 `REACHY_WHISPER_MODELS` 환경변수를 지정하세요. 다른 터미널에서 다음 연결을 유지합니다.

```sh
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 \
  -R 127.0.0.1:18766:127.0.0.1:8766 pollen@reachy-mini.local
```

도우미와 터널은 루프백 주소에만 바인딩합니다. Reachy Mini Control의 설치 앱에서 `reachy_korean_intake`를 실행하고 **문진 시작**을 누르세요. 직접 화면 주소는 `http://reachy-mini.local:7860/`입니다. 다른 Conversation 앱과 동시에 실행하지 마세요.

## 개발 및 확인

공식 Conversation 앱 생성 템플릿에서 파생되었습니다. Apache-2.0 원본 라이선스는 `LICENSE`에 유지합니다. 프로필 데이터 패키지도 독립 이름으로 분리하여 기존 앱 파일을 덮어쓰지 않습니다.

```sh
uv sync --group dev --extra companion
uv run ruff check .
uv run ruff format --check .
uv run mypy --pretty --show-error-codes
uv run pytest tests/ -v
uv build
```

일반 프로필 엔진 회귀 테스트는 템플릿 원본의 잠금 없는 설정에서 실행하고, 한국어 앱 동작은 별도 테스트에서 확인합니다. `REACHY_KOREAN_STT_URL`로 도우미 주소를 바꿀 수 있습니다(기본 `http://127.0.0.1:18766/transcribe`).

## 배포 범위

0.1.0은 Mac 도우미를 사용하는 개인 로봇 설치용 초기 버전입니다. Hugging Face 공개 게시 및 앱 스토어 등록은 별도 단계입니다. 인터넷 서비스 가용성·인식 지연·실제 사용자 발화 다양성을 추가 검증한 뒤 공개 배포하세요.

## 팀원과 소스 코드 공유하기

이 저장소는 수정 가능한 소스 코드입니다. `.exe`나 `.dmg` 설치 앱은 포함하지 않습니다.

### 내려받기와 수정

Git이 있으면 다음 명령으로 받습니다. Git이 없으면 GitHub의 **Code → Download ZIP**으로 받아 압축을 풀고 VS Code에서 폴더를 여세요.

```sh
git clone https://github.com/jhlee8568/reachy-korean-intake.git
cd reachy-korean-intake
```

Python 3.12와 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 준비한 다음, 위의 개발 및 확인 명령으로 의존성을 설치합니다. 명령은 Mac 터미널과 Windows PowerShell에서 동일합니다. 로봇 없이도 코드를 편집할 수 있으며, 음성·동작의 최종 확인에는 공용 로봇이 필요합니다. Windows 실기기 실행은 아직 검증하지 않았습니다.

| 수정할 내용 | 파일 |
|---|---|
| 문진 순서와 답변 처리 | `src/reachy_korean_intake/intake_flow.py` |
| 한국어 인식 처리 | `src/reachy_korean_intake/korean_input.py`, `companion.py` |
| 대화 지침 | `profiles/_korean_intake/profile.md` |
| 사용자 화면 | `src/reachy_korean_intake/static/index.html` |
| 앱 시작과 연결 | `src/reachy_korean_intake/main.py` |

### 수정 내용을 함께 반영하기

공개 저장소이므로 주소를 아는 사람은 로그인 없이 내려받을 수 있습니다. 쓰기 권한이 없는 팀원은 **Fork**로 자신의 사본을 만든 뒤 수정하고 **Pull request**로 변경 내용을 제안하세요. 관리자가 검토해 합칩니다. 원본 저장소에 직접 브랜치를 올리려면 관리자가 해당 팀원의 GitHub 아이디를 Collaborator로 초대해야 합니다.

원본에 쓰기 권한이 있다면 다음처럼 작업합니다.

```sh
git switch -c feat/my-change
# 코드 수정 및 위의 검사 명령 실행
git add <수정한-파일>
git commit -m "변경 내용 설명"
git push -u origin feat/my-change
```

GitHub에서 Pull request를 열고 팀원이 검토한 뒤 합칩니다. 다음 작업 전에 `main`으로 돌아와 `git pull`로 최신 코드를 받으세요.

### 공용 로봇에 반영하기

코드 수정만으로 로봇 앱이 바뀌지는 않습니다. `uv build`로 만든 `dist/`의 wheel을 로봇에 복사하고, 기존 설치 안내에 따라 설치한 다음 앱을 재시작하세요. 한 명이 배포를 담당하고 사용 중인 팀원과 시간을 맞추세요. 인식 도우미와 SSH 터널은 한 번에 컴퓨터 한 대에서만 실행합니다.

`.env`, 로그인 토큰, SSH 키, 음성·문진 기록과 모델 캐시는 저장소에 올리지 마세요. 원본 Apache-2.0 라이선스는 `LICENSE`에 포함되어 있습니다.
