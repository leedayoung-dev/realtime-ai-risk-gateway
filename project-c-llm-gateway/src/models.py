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


class SecurityInfo(BaseModel):
    enabled: bool = False
    available: bool = False
    final_action: Optional[str] = None
    risk_score: Optional[float] = None
    reasons: list[str] = Field(default_factory=list)
    safe_prompt: Optional[str] = None
    safe_output: Optional[str] = None
    masked: bool = False
    gateway_url: Optional[str] = None


class ChatRequest(BaseModel):
    prompt: str
    user_id: str = "anonymous"
    force_fallback: bool = False
    simulate_primary_failure: bool = False
    enable_security: Optional[bool] = None  # None → settings.security_enabled


class ChatResponse(BaseModel):
    request_type: RequestType
    primary_model: ModelName
    used_model: ModelName
    fallback_used: bool
    fallback_reason: Optional[str] = None
    content: str
    latency_ms: int
    cost_usd: float
    blocked: bool = False
    security: Optional[SecurityInfo] = None
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


class AgentToolGuardResult(BaseModel):
    tool: str
    arguments: dict = Field(default_factory=dict)
    enabled: bool = True
    available: bool = False
    action: str = "block"
    allowed: bool = False
    risk_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    danger_labels: list[str] = Field(default_factory=list)
    safe_arguments: Optional[dict] = None
    gateway_url: Optional[str] = None


class AgentToolTrace(BaseModel):
    call_id: str
    tool: str
    arguments: dict = Field(default_factory=dict)
    rationale: str = ""
    guard: Optional[AgentToolGuardResult] = None
    executed: bool = False
    result: Optional[dict] = None
    status: str = "planned"


class AgentRunRequest(BaseModel):
    prompt: str
    user_id: str = "agent"
    enable_security: Optional[bool] = None


class AgentRunResponse(BaseModel):
    prompt: str
    traces: list[AgentToolTrace] = Field(default_factory=list)
    chat: ChatResponse
    tools_planned: int = 0
    tools_executed: int = 0
    tools_blocked: int = 0
    tools_review: int = 0
    created_at: datetime = Field(default_factory=utcnow)