"""Risk insight generation from Project A/B events."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.models import ChatResponse, utcnow
from src.routing.engine import route_chat


class RiskInsightRequest(BaseModel):
    source: str  # news | fraud
    entity_id: str
    risk_score: float
    label: str = "high"
    signals: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    intent: str = "alert_summary"
    user_id: str = "insights"
    enable_security: Optional[bool] = None


class RiskInsight(BaseModel):
    source: str
    entity_id: str
    risk_score: float
    label: str
    signals: list[str] = Field(default_factory=list)
    prompt: str
    summary: str
    chat: ChatResponse
    created_at: datetime = Field(default_factory=utcnow)


def build_insight_prompt(req: RiskInsightRequest) -> str:
    signals = ", ".join(req.signals) if req.signals else "(none)"
    ctx_bits = []
    for key in ("title", "source", "summary", "user_id", "label_hint"):
        if key in req.context and req.context[key] is not None:
            ctx_bits.append(f"{key}={req.context[key]}")
    context_line = "; ".join(ctx_bits) if ctx_bits else "(no extra context)"

    if req.source == "news":
        header = "[뉴스 신뢰도 알림]"
        role = "편집자/SOC용"
    elif req.source == "fraud":
        header = "[사기 탐지 알림]"
        role = "운영/리스크팀용"
    else:
        header = f"[{req.source} 리스크 알림]"
        role = "운영자용"

    return (
        f"{header}\n"
        f"entity={req.entity_id} risk={req.risk_score} label={req.label}\n"
        f"signals={signals}\n"
        f"context: {context_line}\n"
        f"위 근거로 {role} 한국어 요약 3문장과 권장 액션 1줄을 작성하세요."
    )


def generate_insight(req: RiskInsightRequest) -> RiskInsight:
    prompt = build_insight_prompt(req)
    chat = route_chat(
        prompt,
        user_id=req.user_id,
        enable_security=req.enable_security,
        persist=True,
    )
    return RiskInsight(
        source=req.source,
        entity_id=req.entity_id,
        risk_score=req.risk_score,
        label=req.label,
        signals=list(req.signals),
        prompt=prompt,
        summary=chat.content,
        chat=chat,
    )
