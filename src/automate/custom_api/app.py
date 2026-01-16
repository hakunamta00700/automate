"""Custom API FastAPI 애플리케이션"""

import time
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

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


def create_app() -> FastAPI:
    """Custom API FastAPI 애플리케이션 생성

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
    async def chat_completions(request: ChatCompletionRequest):
        """통합 Chat Completions 엔드포인트

        model 파라미터로 사용할 Provider를 선택합니다.
        """
        try:
            provider = get_provider(request.model)
            provider_name = type(provider).__name__
            message_count = len(request.messages)
            logger.info(
                f"Chat completion 처리 시작 - Provider: {provider_name}, "
                f"Model: {request.model}, Messages: {message_count}, "
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
    async def chat_completions_stream(request: ChatCompletionRequest):
        """스트리밍 Chat Completions 엔드포인트"""
        try:
            provider = get_provider(request.model)
            provider_name = type(provider).__name__
            logger.info(
                f"Streaming chat completion 처리 시작 - "
                f"Provider: {provider_name}, Model: {request.model}"
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
    async def codex_completions(request: ChatCompletionRequest):
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
    async def opencode_completions(request: ChatCompletionRequest):
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
    async def gemini_completions(request: ChatCompletionRequest):
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
    async def cursor_completions(request: ChatCompletionRequest):
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
