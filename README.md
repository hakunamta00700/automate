# Automate

YouTube 영상 대본 추출, 요약, 저장 및 텔레그램 봇 기능을 제공하는 자동화 도구입니다.

## 주요 기능

- 🎬 **YouTube 대본 추출**: YouTube 영상의 자막을 다양한 언어로 추출
- 📝 **AI 요약**: OpenAI API를 사용한 영상 대본 요약
- 💾 **Airtable 저장**: 요약된 내용을 Airtable에 자동 저장
- 🤖 **텔레그램 봇**: 텔레그램을 통한 YouTube 영상 요약 및 쇼츠 처리
- 🚀 **FastAPI 서버**: 웹훅을 통한 텔레그램 봇 서비스
- 🔄 **GitHub Workflow 연동**: GitHub Actions를 통한 원격 작업 처리
- 🔌 **Custom API**: Codex, OpenCode, Gemini, Cursor CLI 등을 OpenAI API 스타일로 제공

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
# OpenAI API (요약 기능 사용 시)
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
# OpenAI 모델 설정 (기본값: "gpt-4.1-mini")
OPENAI_MODEL_NAME=gpt-4.1-mini

# OpenAI 입력 토큰 한도 (기본값: 128000)
OPENAI_MAX_INPUT_TOKENS=128000

# GitHub Workflow (dispatch 기능 사용 시)
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name

# Custom API 설정 (선택)
# Codex 명령어 경로 (기본값: 자동 탐색 또는 "codex")
# 일반적인 경로: /home/ubuntu/.npm-global/bin/codex
CODEX_COMMAND=/home/ubuntu/.npm-global/bin/codex
OPENCODE_COMMAND=opencode
CURSOR_COMMAND=cursor
GEMINI_API_KEY=your_gemini_api_key
CUSTOM_API_HOST=0.0.0.0
CUSTOM_API_PORT=8001
CUSTOM_API_TIMEOUT=300
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

#### 8. Custom API 서버 실행

```bash
# 개발 환경 (기본값)
automate custom-api dev

# 운영 환경
automate custom-api prod

# 운영 환경에서 host와 port 지정
automate custom-api prod --host 0.0.0.0 --port 8080

# port만 지정
automate custom-api prod --port 9000
```

OpenAI API 스타일의 인터페이스로 로컬 AI 도구들(Codex, OpenCode, Gemini, Cursor CLI)에 접근할 수 있는 API 서버를 실행합니다.

**환경별 차이:**
- `dev`: 디버그 모드, 자세한 로깅, 자동 리로드, **기본 Provider: Codex**
- `prod`: 최적화된 성능, 멀티프로세스 워커

**옵션:**
- `--host`: 서버 호스트 지정 (기본값: 환경 변수 `CUSTOM_API_HOST` 또는 `0.0.0.0`)
- `--port`: 서버 포트 지정 (기본값: 환경 변수 `CUSTOM_API_PORT` 또는 `8001`)

**기본 Provider 설정:**
- 개발 환경(`dev`)에서는 `model` 파라미터를 생략하면 자동으로 Codex Provider가 사용됩니다.
- 운영 환경(`prod`)에서도 기본 Provider는 Codex입니다.

**API 엔드포인트:**
- `POST /v1/chat/completions`: 통합 엔드포인트 (model 파라미터로 선택)
- `POST /v1/codex/completions`: Codex 전용
- `POST /v1/opencode/completions`: OpenCode 전용
- `POST /v1/gemini/completions`: Gemini 전용
- `POST /v1/cursor/completions`: Cursor CLI 전용
- `GET /v1/models`: 사용 가능한 모델 목록
- `GET /health`: 헬스 체크

## Custom API 사용 가이드

### 빠른 시작

서버를 시작한 후, 기본적인 요청을 보내보세요:

```bash
# 서버 시작
automate custom-api dev

# 간단한 요청 (model 파라미터 생략 가능 - 기본값: codex)
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'

# 또는 명시적으로 codex 지정
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

**Codex Provider 체크 스크립트:**
```bash
# Custom API가 Codex 기반으로 정상 작동하는지 확인
python try_check_custom_api_codex.py
```

### API 엔드포인트 상세

#### 통합 엔드포인트
- **POST** `/v1/chat/completions`: 모든 모델을 지원하는 통합 엔드포인트
  - `model` 파라미터로 사용할 Provider 선택 (codex, opencode, gemini, cursor)
  - `model` 파라미터를 생략하면 기본 Provider(Codex)가 사용됩니다

#### 모델별 전용 엔드포인트
- **POST** `/v1/codex/completions`: Codex 전용
- **POST** `/v1/opencode/completions`: OpenCode 전용
- **POST** `/v1/gemini/completions`: Gemini 전용
- **POST** `/v1/cursor/completions`: Cursor CLI 전용

#### 기타 엔드포인트
- **GET** `/v1/models`: 사용 가능한 모델 목록 조회
- **GET** `/health`: 서버 헬스 체크

### 요청/응답 형식

#### 요청 형식
```json
{
  "model": "codex",                    // 선택적, 기본값: "codex" (dev 환경)
  "messages": [
    {"role": "system", "content": "..."},  // 선택적
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."} // 대화형 대화에서 사용
  ],
  "temperature": 1.0,                 // 선택적, 기본값: 1.0
  "max_tokens": 1000,                  // 선택적
  "stream": false                      // 선택적, 기본값: false
}
```

**참고:** `model` 파라미터를 생략하면 개발 환경(`dev`)에서는 자동으로 Codex Provider가 사용됩니다.

#### 응답 형식
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "codex",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "응답 내용..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 사용 예시

#### 1. 기본 사용법

**curl 예시:**
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "Python으로 Hello World를 출력하는 코드를 작성해줘"}
    ]
  }'
```

**Python 예시:**
```python
import requests

response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={
        "model": "codex",
        "messages": [
            {"role": "user", "content": "Python으로 Hello World를 출력하는 코드를 작성해줘"}
        ]
    }
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

**JavaScript/TypeScript 예시:**
```javascript
const response = await fetch("http://localhost:8001/v1/chat/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "codex",
    messages: [
      { role: "user", content: "Python으로 Hello World를 출력하는 코드를 작성해줘" }
    ]
  })
});

const result = await response.json();
console.log(result.choices[0].message.content);
```

#### 2. 모델별 사용 예시

**Codex 사용:**
```bash
curl -X POST http://localhost:8001/v1/codex/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "FastAPI로 간단한 REST API를 만들어줘"}
    ]
  }'
```

**OpenCode 사용:**
```bash
curl -X POST http://localhost:8001/v1/opencode/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "React 컴포넌트를 작성해줘"}
    ]
  }'
```

**Gemini 사용:**
```bash
curl -X POST http://localhost:8001/v1/gemini/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "머신러닝에 대해 설명해줘"}
    ],
    "temperature": 0.7
  }'
```

**Cursor 사용:**
```bash
curl -X POST http://localhost:8001/v1/cursor/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "TypeScript 타입 정의를 작성해줘"}
    ]
  }'
```

#### 3. 시스템 프롬프트 사용

시스템 프롬프트를 사용하여 AI의 역할과 동작을 정의할 수 있습니다:

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "system", "content": "당신은 전문 Python 개발자입니다. 간결하고 명확한 코드를 작성합니다."},
      {"role": "user", "content": "리스트에서 중복을 제거하는 함수를 작성해줘"}
    ]
  }'
```

**번역기 예시:**
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "system", "content": "당신은 전문 번역가입니다. 자연스럽고 정확한 번역을 제공합니다."},
      {"role": "user", "content": "Hello, how are you?를 한국어로 번역해줘"}
    ]
  }'
```

#### 4. 대화형 대화 (Multi-turn Conversation)

여러 메시지를 주고받는 대화를 구현할 수 있습니다:

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "Python에서 리스트와 튜플의 차이점은?"},
      {"role": "assistant", "content": "리스트는 변경 가능하고, 튜플은 불변입니다..."},
      {"role": "user", "content": "그럼 언제 리스트를 사용하고 언제 튜플을 사용하나요?"}
    ]
  }'
```

**Python 클라이언트 예시:**
```python
import requests

conversation = [
    {"role": "user", "content": "Python에서 리스트와 튜플의 차이점은?"}
]

# 첫 번째 메시지
response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={"model": "codex", "messages": conversation}
)
result = response.json()
assistant_message = result["choices"][0]["message"]["content"]
print(f"Assistant: {assistant_message}")

# 대화에 추가
conversation.append({"role": "assistant", "content": assistant_message})
conversation.append({"role": "user", "content": "그럼 언제 리스트를 사용하고 언제 튜플을 사용하나요?"})

# 두 번째 메시지
response = requests.post(
    "http://localhost:8001/v1/chat/completions",
    json={"model": "codex", "messages": conversation}
)
result = response.json()
print(f"Assistant: {result['choices'][0]['message']['content']}")
```

#### 5. 스트리밍 사용

Server-Sent Events (SSE)를 사용하여 실시간으로 응답을 받을 수 있습니다:

```bash
curl -X POST http://localhost:8001/v1/chat/completions/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "Python에 대해 자세히 설명해줘"}
    ],
    "stream": true
  }'
```

**Python 클라이언트 예시:**
```python
import requests
import json

response = requests.post(
    "http://localhost:8001/v1/chat/completions/stream",
    json={
        "model": "codex",
        "messages": [
            {"role": "user", "content": "Python에 대해 자세히 설명해줘"}
        ],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode("utf-8")
        if line_str.startswith("data: "):
            data_str = line_str[6:]  # "data: " 제거
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("delta", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
            except json.JSONDecodeError:
                pass
print()  # 줄바꿈
```

**JavaScript 클라이언트 예시:**
```javascript
const response = await fetch("http://localhost:8001/v1/chat/completions/stream", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "codex",
    messages: [
      { role: "user", content: "Python에 대해 자세히 설명해줘" }
    ],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const dataStr = line.slice(6);
      if (dataStr === "[DONE]") return;

      try {
        const data = JSON.parse(dataStr);
        if (data.choices?.[0]?.delta?.content) {
          process.stdout.write(data.choices[0].delta.content);
        }
      } catch (e) {
        // JSON 파싱 오류 무시
      }
    }
  }
}
```

#### 6. 파라미터 튜닝

**temperature 설정:**
- `0.0`: 가장 결정적이고 일관된 응답
- `1.0`: 기본값, 균형잡힌 창의성
- `2.0`: 매우 창의적이고 다양한 응답

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "창의적인 스토리를 작성해줘"}
    ],
    "temperature": 1.5
  }'
```

**max_tokens 설정:**
응답의 최대 길이를 제한합니다:

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "codex",
    "messages": [
      {"role": "user", "content": "간단히 설명해줘"}
    ],
    "max_tokens": 100
  }'
```

### 에러 처리

#### 일반적인 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

#### 주요 에러 케이스

**400 Bad Request:**
- 지원하지 않는 모델 사용
- 잘못된 요청 형식

```bash
# 잘못된 모델 사용
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "invalid-model",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
# 응답: {"detail": "지원하지 않는 모델: invalid-model. 지원 모델: codex, opencode, gemini, cursor"}
```

**500 Internal Server Error:**
- Provider 실행 실패
- 타임아웃 발생
- 기타 서버 오류

**Python 에러 처리 예시:**
```python
import requests

try:
    response = requests.post(
        "http://localhost:8001/v1/chat/completions",
        json={
            "model": "codex",
            "messages": [{"role": "user", "content": "Hello"}]
        },
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    print(result["choices"][0]["message"]["content"])
except requests.exceptions.HTTPError as e:
    print(f"HTTP 오류: {e}")
    if e.response:
        print(f"상세: {e.response.json()}")
except requests.exceptions.Timeout:
    print("요청 타임아웃")
except requests.exceptions.RequestException as e:
    print(f"요청 오류: {e}")
```

### 문제 해결 가이드

#### 서버가 시작되지 않는 경우
1. 포트가 이미 사용 중인지 확인: `netstat -an | grep 8001`
2. 환경 변수 설정 확인: `.env` 파일 확인
3. 로그 확인: `automate custom-api dev` 실행 시 로그 확인

#### Provider 실행 실패
1. 각 CLI 도구가 PATH에 있는지 확인:
   ```bash
   which codex
   which opencode
   which cursor
   ```
2. 명령어 경로를 환경 변수로 설정:
   ```env
   CODEX_COMMAND=/path/to/codex
   OPENCODE_COMMAND=/path/to/opencode
   CURSOR_COMMAND=/path/to/cursor
   ```

#### 타임아웃 오류
- `CUSTOM_API_TIMEOUT` 환경 변수로 타임아웃 시간 조정 (기본값: 300초)

#### 로깅 확인
- 개발 환경: `automate custom-api dev` - DEBUG 레벨 로그
- 운영 환경: `automate custom-api prod` - INFO 레벨 로그
- 로그는 stderr로 출력됩니다
- 서버 시작 시 기본 Provider 정보가 로그에 표시됩니다

#### Codex Provider 테스트
프로젝트 루트에 `try_check_custom_api_codex.py` 스크립트를 실행하여 Codex Provider가 정상 작동하는지 확인할 수 있습니다:

```bash
# 서버가 실행 중인 상태에서
python try_check_custom_api_codex.py
```

이 스크립트는 다음을 확인합니다:
- 서버 헬스 체크
- 모델 목록에 Codex 포함 여부
- 기본 Provider가 Codex인지 확인
- Codex 모델 명시적 지정 테스트
- Codex 전용 엔드포인트 테스트
- Codex 시스템 프롬프트, 스트리밍, 파라미터 튜닝 등 기능 테스트

### 고급 사용법

#### httpx를 사용한 비동기 Python 클라이언트

```python
import asyncio
import httpx

async def chat_completion():
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8001/v1/chat/completions",
            json={
                "model": "codex",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

# 사용
result = asyncio.run(chat_completion())
print(result)
```

#### 여러 요청 동시 처리

```python
import asyncio
import httpx

async def multiple_requests():
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = [
            client.post(
                "http://localhost:8001/v1/chat/completions",
                json={
                    "model": "codex",
                    "messages": [{"role": "user", "content": f"질문 {i}"}]
                }
            )
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

results = asyncio.run(multiple_requests())
```

#### 모델 목록 조회

```bash
curl http://localhost:8001/v1/models
```

**Python 예시:**
```python
import requests

response = requests.get("http://localhost:8001/v1/models")
models = response.json()
print(f"사용 가능한 모델: {[m['id'] for m in models['data']]}")
```

#### 9. 대본 추출 스크립트 (직접 실행)

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
- `automate.services.summary`: AI 요약 기능 (OpenAI API)
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
- `automate.custom_api`: Custom API 서버
  - `create_app`: FastAPI 애플리케이션 생성
  - `providers`: AI 도구별 Provider 구현 (Codex, OpenCode, Gemini, Cursor)
  - OpenAI API 스타일의 인터페이스 제공

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
│       │       ├── serve.py          # 서버 실행
│       │       └── custom_api.py     # Custom API 서버 실행
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
│       ├── custom_api/                # Custom API 서버
│       │   ├── app.py                 # FastAPI 애플리케이션
│       │   ├── models.py              # 요청/응답 모델
│       │   ├── config.py              # 설정 관리
│       │   └── providers/             # AI Provider 구현
│       │       ├── base.py            # 추상 베이스 클래스
│       │       ├── codex.py          # Codex Provider
│       │       ├── opencode.py       # OpenCode Provider
│       │       ├── gemini.py         # Gemini Provider
│       │       └── cursor.py         # Cursor Provider
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
- `custom-api`: 각 AI 도구의 CLI 명령어가 PATH에 있어야 함 (선택적으로 `GEMINI_API_KEY` 설정)

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

