# Automate

YouTube 영상 대본 추출, 요약, 저장 및 텔레그램 봇 기능을 제공하는 자동화 도구입니다.

## 주요 기능

- 🎬 **YouTube 대본 추출**: YouTube 영상의 자막을 다양한 언어로 추출
- 📝 **AI 요약**: Gemini API를 사용한 영상 대본 요약
- 💾 **Airtable 저장**: 요약된 내용을 Airtable에 자동 저장
- 🤖 **텔레그램 봇**: 텔레그램을 통한 YouTube 영상 요약 및 쇼츠 처리
- 🚀 **FastAPI 서버**: 웹훅을 통한 텔레그램 봇 서비스
- 🔄 **GitHub Workflow 연동**: GitHub Actions를 통한 원격 작업 처리

## 요구사항

- Python >= 3.12
- uv (패키지 관리자)

## 설치

### 1. 저장소 클론

```bash
git clone <repository-url>
cd automate
```

### 2. 패키지 설치

```bash
# uv를 사용한 설치
uv pip install -e .

# 또는 개발 의존성 포함
uv pip install -e ".[dev]"
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

### 필수 환경 변수

```env
# OpenAI API (필요한 경우)
OPENAI_API_KEY=your_openai_api_key

# Airtable 설정
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_NAME=your_base_name
AIRTABLE_TABLE_NAME=your_table_name

# 텔레그램 봇 설정
BOT_TOKEN=your_telegram_bot_token
CHANNEL_CHAT_ID=your_channel_chat_id

# 웹훅 설정 (FastAPI 서버 사용 시)
WEBHOOK_DOMAIN=your_webhook_domain
WEBHOOK_PATH=/webhook
```

### 선택적 환경 변수

```env
# Google Gemini API (요약 기능 사용 시)
GOOGLE_API_KEY=your_google_api_key

# LLM 모델 선택 (기본값: "gemini")
TARGET_LLM_MODEL=gemini

# GitHub Workflow (dispatch 기능 사용 시)
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
```

## 사용법

### CLI 명령어

#### 1. 비디오 ID로 전사 및 요약

```bash
automate transcribe --video-id <VIDEO_ID> --language ko
```

**옵션:**
- `--video-id`: YouTube 비디오 ID (필수)
- `--language`: 자막 언어 코드 (기본값: `ko`)

**지원 언어:**
- `ko`: 한국어
- `en`: 영어
- `ja`: 일본어
- `zh-Hans`: 중국어(간체)
- `zh-Hant`: 중국어(번체)
- 기타 YouTube에서 지원하는 언어 코드

#### 2. URL로 전사 및 요약

```bash
automate transcribe-from-url "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### 3. URL에서 비디오 ID 추출

```bash
automate get-video-id-from-url "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### 4. FastAPI 서버 실행

```bash
# 개발 환경 (기본값)
automate serve dev

# 운영 환경
automate serve prod
```

**환경별 차이:**
- `dev`: 디버그 모드, 자세한 로깅, 리로더 활성화
- `prod`: 최적화된 성능, 멀티프로세스 워커

#### 5. 텔레그램 풀링 봇 실행

```bash
automate telegram-bot
```

텔레그램 메시지를 수신하여 YouTube 영상 요약 및 쇼츠 처리를 수행합니다. 오류 발생 시 자동으로 재시작됩니다.

**사용 방법:**
- `요약|<YouTube URL>`: 영상 요약 요청
- `쇼츠|<URL>`: 쇼츠 대본 생성 요청

#### 6. GitHub Workflow Dispatch

```bash
automate dispatch "https://www.youtube.com/watch?v=VIDEO_ID"
```

GitHub Actions의 workflow를 트리거하여 원격에서 비디오 전사를 실행합니다.

**필수 환경 변수:**
- `GITHUB_TOKEN`
- `GITHUB_OWNER`
- `GITHUB_REPO`

#### 7. 텔레그램 메시지 전송

```bash
automate send-telegram "메시지 내용"
```

설정된 텔레그램 채널에 메시지를 전송합니다.

#### 8. 대본 추출 스크립트 (직접 실행)

```bash
python -m automate.scripts.get_transcript "https://www.youtube.com/watch?v=VIDEO_ID"
```

YouTube 영상의 대본을 시간 포맷을 포함하여 추출하고 `transcript.txt` 파일로 저장합니다.

### Python 모듈로 사용

```python
import asyncio
from automate.services.youtube import process_video, extract_video_id, get_transcript
from automate.services.summary import summarize
from automate.services.airtable import save_to_airtable

# 비디오 ID 추출
video_id = extract_video_id("https://www.youtube.com/watch?v=VIDEO_ID")

# 비디오 처리 (대본 추출, 요약, Airtable 저장)
async def main():
    summary = await process_video(video_id, language="ko")
    print(summary)

asyncio.run(main())
```

**주요 모듈:**
- `automate.services.youtube`: YouTube 대본 추출 및 처리
  - `extract_video_id`: YouTube URL에서 비디오 ID 추출
  - `get_transcript`: 대본 추출
  - `get_youtube_metadata`: 비디오 메타데이터 추출
  - `process_video`: 전체 처리 (대본 추출, 요약, 저장)
- `automate.services.summary`: AI 요약 기능 (Gemini API)
  - `summarize`: 대본 요약 생성
  - `format_transcript`: 대본 포맷팅
- `automate.services.airtable`: Airtable 연동
  - `save_to_airtable`: Airtable에 데이터 저장
- `automate.services.telegram`: 텔레그램 봇 및 메시지 전송
  - `run_with_restart`: 풀링 봇 실행
  - `send_message`: 메시지 전송
  - `create_app`: FastAPI 웹훅 앱 생성
- `automate.utils`: 공통 유틸리티
  - `to_async`: 동기 함수를 비동기로 변환하는 데코레이터
  - `extract_video_id`: YouTube URL 추출 유틸리티
  - `format_transcript_with_timestamps`: 타임스탬프 포함 대본 포맷팅
- `automate.core`: 설정 및 상수
  - `Settings`: 환경 변수 설정 관리
  - `get_settings`: 설정 인스턴스 반환

## 프로젝트 구조

```
automate/
├── src/
│   └── automate/
│       ├── __init__.py              # 패키지 진입점
│       ├── cli/                      # CLI 모듈
│       │   ├── __init__.py
│       │   ├── main.py               # CLI 진입점
│       │   ├── utils.py              # CLI 공통 유틸리티
│       │   └── commands/             # 명령어별 분리
│       │       ├── transcribe.py     # 전사 명령어
│       │       ├── telegram.py       # 텔레그램 명령어
│       │       ├── dispatch.py       # GitHub workflow dispatch
│       │       └── serve.py          # 서버 실행
│       ├── core/                      # 설정 및 상수
│       │   ├── __init__.py
│       │   ├── config.py              # 환경 변수 통합 관리
│       │   └── constants.py          # 상수 정의
│       ├── services/                  # 서비스 레이어
│       │   ├── youtube/               # YouTube 서비스
│       │   │   ├── extractor.py       # 비디오 ID 추출
│       │   │   ├── transcript.py      # 대본 추출
│       │   │   ├── metadata.py        # 메타데이터 추출
│       │   │   └── processor.py       # 비디오 처리
│       │   ├── airtable/              # Airtable 서비스
│       │   │   ├── client.py          # Airtable 클라이언트
│       │   │   └── repository.py      # 데이터 저장
│       │   ├── summary/               # 요약 서비스
│       │   │   ├── formatter.py       # 대본 포맷팅
│       │   │   ├── generator.py      # AI 요약 생성
│       │   │   └── prompt.py          # 프롬프트 관리
│       │   └── telegram/              # 텔레그램 서비스
│       │       ├── bot.py             # 풀링 봇
│       │       ├── sender.py          # 메시지 전송
│       │       └── webhook.py         # FastAPI 웹훅
│       ├── utils/                     # 공통 유틸리티
│       │   ├── __init__.py
│       │   ├── async_utils.py         # 비동기 유틸리티
│       │   ├── youtube_utils.py       # YouTube 유틸리티
│       │   └── transcript_utils.py    # 대본 포맷팅 유틸리티
│       └── scripts/                   # 독립 실행 스크립트
│           └── get_transcript.py      # 대본 추출 스크립트
├── pyproject.toml                     # 프로젝트 설정
└── README.md                          # 프로젝트 문서
```

## 주의사항

### 환경 변수 필수 여부

일부 CLI 명령어는 특정 환경 변수가 필수입니다:
- `transcribe`, `transcribe-from-url`: 모든 필수 환경 변수 필요
- `telegram-bot`: `BOT_TOKEN`, `CHANNEL_CHAT_ID` 필요
- `dispatch`: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO` 필요
- `send-telegram`: `BOT_TOKEN` 필요
- `serve`: `BOT_TOKEN`, `WEBHOOK_DOMAIN`, `WEBHOOK_PATH` 필요

### 비동기 함수 사용

대부분의 함수는 비동기(`async`)로 구현되어 있습니다. Python 모듈로 사용할 때는 `asyncio.run()` 또는 `await`를 사용해야 합니다.

## 개발

### 개발 의존성 설치

```bash
uv pip install -e ".[dev]"
```

### 코드 포맷팅

```bash
# Black으로 포맷팅
black src/

# isort로 import 정렬
isort src/

# autoflake로 미사용 import 제거
autoflake --in-place --remove-all-unused-imports --recursive src/
```

## 라이선스

Private project

## 작성자

David Cho (csi00700@gmail.com)

