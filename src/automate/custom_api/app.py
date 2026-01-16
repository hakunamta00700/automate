"""Custom API FastAPI 애플리케이션"""

import time
from collections.abc import Callable

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_custom_api_settings
from .models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelInfo,
    ModelsListResponse,
)
from .providers.base import BaseProvider
from .providers.codex import CodexProvider
from .providers.cursor import CursorProvider
from .providers.gemini import GeminiProvider
from .providers.opencode import OpenCodeProvider

# API Key 헤더 설정
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_provider(model: str) -> BaseProvider:
    """모델 이름에 따라 Provider 인스턴스 반환

    Args:
        model: 모델 이름

    Returns:
        BaseProvider 인스턴스

    Raises:
        HTTPException: 지원하지 않는 모델인 경우
    """
    providers: dict[str, BaseProvider] = {
        "codex": CodexProvider(),
        "opencode": OpenCodeProvider(),
        "gemini": GeminiProvider(),
        "cursor": CursorProvider(),
    }

    if model not in providers:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 모델: {model}. 지원 모델: {', '.join(providers.keys())}",
        )

    provider = providers[model]
    provider_name = type(provider).__name__
    logger.info(f"Provider 선택됨: {provider_name} (model: {model})")
    return provider


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅을 위한 Middleware"""

    async def dispatch(self, request: Request, call_next: Callable):
        """요청과 응답을 로깅합니다."""
        start_time = time.time()

        # 요청 정보 로깅
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"요청 수신: {method} {path} (IP: {client_ip})")

        # 요청 본문 로깅 (POST 요청만, 일부 경로 제외)
        if method == "POST" and path not in ["/health"]:
            try:
                body = await request.body()
                if body:
                    # 본문이 너무 길면 잘라서 로깅
                    body_str = body.decode("utf-8", errors="ignore")
                    if len(body_str) > 500:
                        logger.debug(f"요청 본문 (일부): {body_str[:500]}...")
                    else:
                        logger.debug(f"요청 본문: {body_str}")
            except Exception as e:
                logger.warning(f"요청 본문 읽기 실패: {e}")

        # 응답 처리
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            status_code = response.status_code

            # 응답 로깅
            logger.info(
                f"응답 전송: {method} {path} - 상태 코드: {status_code}, "
                f"처리 시간: {process_time:.3f}초"
            )

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.exception(
                f"요청 처리 중 오류 발생: {method} {path} - "
                f"처리 시간: {process_time:.3f}초, 오류: {e}"
            )
            raise


def create_auth_dependency(require_auth: bool):
    """인증 의존성 생성 함수

    Args:
        require_auth: 인증이 필요한지 여부

    Returns:
        인증 검증 함수
    """

    async def verify_api_key(
        api_key: str | None = Security(api_key_header),
    ) -> None:
        """API Key 검증 함수

        Args:
            api_key: 요청 헤더의 API Key

        Raises:
            HTTPException: 인증 실패 시
        """
        if not require_auth:
            return

        settings = get_custom_api_settings()
        expected_key = settings.CUSTOM_API_KEY

        if not expected_key:
            logger.warning("인증이 활성화되었지만 CUSTOM_API_KEY가 설정되지 않았습니다.")
            raise HTTPException(
                status_code=500,
                detail="서버 설정 오류: API Key가 설정되지 않았습니다.",
            )

        if not api_key:
            logger.warning("API Key가 제공되지 않았습니다.")
            raise HTTPException(
                status_code=401,
                detail="인증이 필요합니다. X-API-Key 헤더를 제공하세요.",
            )

        if api_key != expected_key:
            logger.warning("잘못된 API Key 시도")
            raise HTTPException(
                status_code=403,
                detail="잘못된 API Key입니다.",
            )

        logger.debug("API Key 인증 성공")

    return verify_api_key


def create_app(default_provider: str = "codex", require_auth: bool = False) -> FastAPI:
    """Custom API FastAPI 애플리케이션 생성

    Args:
        default_provider: 기본 provider 이름 (기본값: codex)
        require_auth: 인증이 필요한지 여부 (기본값: False)

    Returns:
        FastAPI 애플리케이션 인스턴스
    """
    app = FastAPI(
        title="Custom API for Local AI Tools",
        description="OpenAI API 스타일의 로컬 AI 도구 API",
        version="1.0.0",
    )

    # 로깅 middleware 추가
    app.add_middleware(LoggingMiddleware)

    # 인증 의존성 생성
    auth_dependency = create_auth_dependency(require_auth)

    logger.info("FastAPI 애플리케이션 생성 완료")

    # 사용 가능한 모델 목록
    AVAILABLE_MODELS = [
        ModelInfo(id="codex", owned_by="custom"),
        ModelInfo(id="opencode", owned_by="custom"),
        ModelInfo(id="gemini", owned_by="custom"),
        ModelInfo(id="cursor", owned_by="custom"),
    ]

    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        logger.debug("헬스 체크 요청")
        return {"status": "healthy"}

    @app.get("/v1/models", response_model=ModelsListResponse)
    async def list_models():
        """사용 가능한 모델 목록 반환"""
        logger.info("모델 목록 요청")
        models = ModelsListResponse(data=AVAILABLE_MODELS)
        logger.debug(f"사용 가능한 모델 수: {len(models.data)}")
        return models

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    async def chat_completions(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """통합 Chat Completions 엔드포인트

        model 파라미터로 사용할 Provider를 선택합니다.
        model이 지정되지 않은 경우 기본 provider를 사용합니다.
        """
        try:
            model = request.model or default_provider
            provider = get_provider(model)
            provider_name = type(provider).__name__
            message_count = len(request.messages)
            logger.info(
                f"Chat completion 처리 시작 - Provider: {provider_name}, "
                f"Model: {model}, Messages: {message_count}, "
                f"Temperature: {request.temperature}, MaxTokens: {request.max_tokens}"
            )
            start_time = time.time()
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            process_time = time.time() - start_time
            response_length = len(response.choices[0].message.content) if response.choices else 0
            # 응답의 model 필드도 업데이트
            response.model = model
            logger.info(
                f"Chat completion 처리 완료 - Provider: {provider_name}, "
                f"처리 시간: {process_time:.3f}초, "
                f"응답 길이: {response_length}자"
            )
            return response
        except RuntimeError as e:
            logger.error(f"Chat completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/v1/chat/completions/stream")
    async def chat_completions_stream(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """스트리밍 Chat Completions 엔드포인트"""
        try:
            model = request.model or default_provider
            provider = get_provider(model)
            provider_name = type(provider).__name__
            logger.info(
                f"Streaming chat completion 처리 시작 - Provider: {provider_name}, Model: {model}"
            )

            async def generate():
                async for chunk in provider.stream_chat_completion(
                    messages=request.messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ):
                    # SSE 형식으로 전송
                    yield f"data: {chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
                logger.info(f"Streaming chat completion 처리 완료 - Provider: {provider_name}")

            return StreamingResponse(generate(), media_type="text/event-stream")
        except RuntimeError as e:
            logger.error(f"Streaming chat completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/v1/codex/completions", response_model=ChatCompletionResponse)
    async def codex_completions(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """Codex 전용 Chat Completions 엔드포인트"""
        try:
            provider = CodexProvider()
            logger.info(f"Codex completion 처리 시작 - Provider: {type(provider).__name__}")
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            logger.info(f"Codex completion 처리 완료 - Provider: {type(provider).__name__}")
            return response
        except RuntimeError as e:
            logger.error(f"Codex completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/v1/opencode/completions", response_model=ChatCompletionResponse)
    async def opencode_completions(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """OpenCode 전용 Chat Completions 엔드포인트"""
        try:
            provider = OpenCodeProvider()
            logger.info(f"OpenCode completion 처리 시작 - Provider: {type(provider).__name__}")
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            logger.info(f"OpenCode completion 처리 완료 - Provider: {type(provider).__name__}")
            return response
        except RuntimeError as e:
            logger.error(f"OpenCode completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/v1/gemini/completions", response_model=ChatCompletionResponse)
    async def gemini_completions(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """Gemini 전용 Chat Completions 엔드포인트"""
        try:
            provider = GeminiProvider()
            logger.info(f"Gemini completion 처리 시작 - Provider: {type(provider).__name__}")
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            logger.info(f"Gemini completion 처리 완료 - Provider: {type(provider).__name__}")
            return response
        except RuntimeError as e:
            logger.error(f"Gemini completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @app.post("/v1/cursor/completions", response_model=ChatCompletionResponse)
    async def cursor_completions(
        request: ChatCompletionRequest,
        _: None = Depends(auth_dependency),
    ):
        """Cursor 전용 Chat Completions 엔드포인트"""
        try:
            provider = CursorProvider()
            logger.info(f"Cursor completion 처리 시작 - Provider: {type(provider).__name__}")
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            logger.info(f"Cursor completion 처리 완료 - Provider: {type(provider).__name__}")
            return response
        except RuntimeError as e:
            logger.error(f"Cursor completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    return app
