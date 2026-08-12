from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RequestType(str, Enum):
    SIMPLE = "simple"
    COMPLEX_REASONING = "complex_reasoning"
    LONG_CONTEXT = "long_context"


class ModelName(str, Enum):
    GPT = "gpt"
    CLAUDE = "claude"
    GEMINI = "gemini"


class ChatRequest(BaseModel):
    prompt: str
    force_fallback: bool = False
    simulate_primary_failure: bool = False


class ChatResponse(BaseModel):
    request_type: RequestType
    primary_model: ModelName
    used_model: ModelName
    fallback_used: bool
    fallback_reason: Optional[str] = None
    content: str
    latency_ms: int
    cost_usd: float
    created_at: datetime = Field(default_factory=utcnow)


class ModelMetrics(BaseModel):
    model: ModelName
    quality: float
    latency_ms: int
    cost_usd: float
    available: bool = True


class EvaluationResult(BaseModel):
    prompt: str
    results: list[ModelMetrics]
    recommended_model: ModelName
