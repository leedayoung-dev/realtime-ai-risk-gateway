"""Security event store + user risk profiling."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from threading import RLock
from typing import Optional

from pydantic import BaseModel, Field

from src.models import AgentGuardResponse, GuardResponse, PolicyAction, utcnow


class SecurityEvent(BaseModel):
    user_id: str
    final_action: PolicyAction
    risk_score: float
    reasons: list[str] = Field(default_factory=list)
    threat_labels: list[str] = Field(default_factory=list)
    dlp_kinds: list[str] = Field(default_factory=list)
    event_type: str = "prompt"  # prompt | agent
    tool: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


_lock = RLock()
_EVENTS: list[SecurityEvent] = []
_MAX = 500


def record_guard(user_id: str, response: GuardResponse) -> SecurityEvent:
    insp = response.input_inspection
    labels: list[str] = []
    for layer in insp.layers:
        labels.extend(layer.labels)
    event = SecurityEvent(
        user_id=user_id,
        final_action=response.final_action,
        risk_score=insp.risk_score,
        reasons=list(insp.reasons),
        threat_labels=labels[:12],
        dlp_kinds=[f.kind for f in insp.dlp_findings],
        event_type="prompt",
    )
    with _lock:
        _EVENTS.append(event)
        if len(_EVENTS) > _MAX:
            del _EVENTS[:-_MAX]
    return event


def record_agent_event(user_id: str, response: AgentGuardResponse) -> SecurityEvent:
    event = SecurityEvent(
        user_id=user_id,
        final_action=response.action,
        risk_score=response.risk_score,
        reasons=list(response.reasons),
        threat_labels=list(response.danger_labels),
        dlp_kinds=[f.kind for f in response.dlp_findings],
        event_type="agent",
        tool=response.call.tool.value,
    )
    with _lock:
        _EVENTS.append(event)
        if len(_EVENTS) > _MAX:
            del _EVENTS[:-_MAX]
    return event


def list_events(limit: int = 50) -> list[SecurityEvent]:
    with _lock:
        return list(_EVENTS[-limit:])[::-1]


def clear_events() -> None:
    with _lock:
        _EVENTS.clear()


def aggregate() -> dict:
    with _lock:
        items = list(_EVENTS)

    total = len(items)
    by_action: dict[str, int] = defaultdict(int)
    blocked = 0
    injectionish = 0
    pii = 0
    credential = 0
    agent_calls = 0
    agent_blocked = 0

    for ev in items:
        by_action[ev.final_action.value] += 1
        if ev.final_action == PolicyAction.BLOCK:
            blocked += 1
        if ev.event_type == "agent":
            agent_calls += 1
            if ev.final_action == PolicyAction.BLOCK:
                agent_blocked += 1
        joined = " ".join(ev.threat_labels + ev.reasons + ev.dlp_kinds).lower()
        if any(x in joined for x in ("inject", "jailbreak", "ignore", "시스템", "프롬프트", "지시")):
            injectionish += 1
        if any(x in ev.dlp_kinds for x in ("phone", "email")) or "pii" in joined:
            pii += 1
        if any(x in ev.dlp_kinds for x in ("aws_secret", "api_key")) or "credential" in joined:
            credential += 1

    return {
        "request_count": total,
        "blocked": blocked,
        "block_rate": round(blocked / total, 3) if total else 0.0,
        "by_action": dict(by_action),
        "prompt_injection_like": injectionish,
        "pii_exposure": pii,
        "credential_leak": credential,
        "agent_calls": agent_calls,
        "agent_blocked": agent_blocked,
    }


def user_profile(user_id: str) -> dict:
    with _lock:
        items = [e for e in _EVENTS if e.user_id == user_id]

    if not items:
        return {
            "user_id": user_id,
            "event_count": 0,
            "risk_score": 0.0,
            "status": "ALLOW",
            "timeline": [],
        }

    score = 0.0
    for ev in items:
        if ev.final_action == PolicyAction.BLOCK:
            score += 28
        elif ev.final_action == PolicyAction.REVIEW:
            score += 14
        elif ev.final_action == PolicyAction.MASK:
            score += 10
        score += min(ev.risk_score * 0.15, 12)
    score = min(100.0, score)
    status = "BLOCKED" if score >= 80 else "REVIEW" if score >= 50 else "ALLOW"

    timeline = [
        {
            "event_type": e.event_type,
            "tool": e.tool,
            "action": e.final_action.value,
            "risk_score": e.risk_score,
            "reasons": e.reasons,
            "created_at": e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else str(e.created_at),
        }
        for e in items[-12:]
    ]
    return {
        "user_id": user_id,
        "event_count": len(items),
        "risk_score": round(score, 1),
        "status": status,
        "timeline": timeline,
    }
