"""Custom API FastAPI 애플리케이션"""


from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

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
        return {"status": "healthy"}

    @app.get("/v1/models", response_model=ModelsListResponse)
    async def list_models():
        """사용 가능한 모델 목록 반환"""
        return ModelsListResponse(data=AVAILABLE_MODELS)

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    async def chat_completions(request: ChatCompletionRequest):
        """통합 Chat Completions 엔드포인트

        model 파라미터로 사용할 Provider를 선택합니다.
        """
        try:
            provider = get_provider(request.model)
            provider_name = type(provider).__name__
            logger.info(f"Chat completion 처리 시작 - Provider: {provider_name}, Model: {request.model}")
            response = await provider.chat_completion(
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            logger.info(f"Chat completion 처리 완료 - Provider: {provider_name}")
            return response
        except RuntimeError as e:
            logger.error(f"Chat completion 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.post("/v1/chat/completions/stream")
    async def chat_completions_stream(request: ChatCompletionRequest):
        """스트리밍 Chat Completions 엔드포인트"""
        try:
            provider = get_provider(request.model)
            provider_name = type(provider).__name__
            logger.info(f"Streaming chat completion 처리 시작 - Provider: {provider_name}, Model: {request.model}")

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
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

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
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

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
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

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
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

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
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.exception(f"예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return app
