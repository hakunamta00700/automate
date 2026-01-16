"""OpenAI API 스타일의 요청/응답 모델"""

from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """채팅 메시지 모델"""

    role: Literal["system", "user", "assistant"] = Field(..., description="메시지 역할")
    content: str = Field(..., description="메시지 내용")


class ChatCompletionRequest(BaseModel):
    """Chat Completion 요청 모델"""

    model: str = Field(..., description="사용할 모델 이름")
    messages: list[ChatMessage] = Field(..., description="메시지 배열")
    temperature: Optional[float] = Field(
        default=1.0, ge=0.0, le=2.0, description="샘플링 온도"
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, description="최대 생성 토큰 수"
    )
    stream: Optional[bool] = Field(default=False, description="스트리밍 응답 여부")


class ChatCompletionMessage(BaseModel):
    """Chat Completion 응답 메시지 모델"""

    role: Literal["assistant"] = Field(..., description="메시지 역할")
    content: str = Field(..., description="메시지 내용")


class Usage(BaseModel):
    """토큰 사용량 모델"""

    prompt_tokens: int = Field(..., description="프롬프트 토큰 수")
    completion_tokens: int = Field(..., description="생성 토큰 수")
    total_tokens: int = Field(..., description="전체 토큰 수")


class ChatCompletionChoice(BaseModel):
    """Chat Completion 선택지 모델"""

    index: int = Field(..., description="선택지 인덱스")
    message: ChatCompletionMessage = Field(..., description="응답 메시지")
    finish_reason: Literal["stop", "length", "error"] = Field(
        ..., description="완료 이유"
    )


class ChatCompletionResponse(BaseModel):
    """Chat Completion 응답 모델"""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid4().hex[:12]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="생성 시간 (Unix timestamp)",
    )
    model: str = Field(..., description="사용된 모델 이름")
    choices: list[ChatCompletionChoice] = Field(..., description="응답 선택지")
    usage: Optional[Usage] = Field(default=None, description="토큰 사용량")


class ModelInfo(BaseModel):
    """모델 정보 모델"""

    id: str = Field(..., description="모델 ID")
    object: Literal["model"] = "model"
    created: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="생성 시간",
    )
    owned_by: str = Field(default="custom", description="소유자")


class ModelsListResponse(BaseModel):
    """모델 목록 응답 모델"""

    object: Literal["list"] = "list"
    data: list[ModelInfo] = Field(..., description="모델 목록")
