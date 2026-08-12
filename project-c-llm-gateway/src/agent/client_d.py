"""Call Project D /v1/agent/guard."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.models import AgentToolGuardResult


def guard_tool_call(
    tool: str,
    arguments: dict[str, Any],
    *,
    user_id: str = "agent",
    call_id: str = "c-call-1",
) -> AgentToolGuardResult:
    url = settings.security_gateway_url.rstrip("/")
    if not settings.security_enabled:
        return AgentToolGuardResult(
            tool=tool,
            arguments=arguments,
            enabled=False,
            available=False,
            action="allow",
            allowed=True,
            risk_score=0.0,
            reasons=["security_disabled"],
            gateway_url=url,
        )

    try:
        payload = {
            "user_id": user_id,
            "call": {"tool": tool, "arguments": arguments, "call_id": call_id},
        }
        with httpx.Client(timeout=settings.security_timeout_ms / 1000) as client:
            resp = client.post(f"{url}/v1/agent/guard", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 — fail-open for demo
        return AgentToolGuardResult(
            tool=tool,
            arguments=arguments,
            enabled=True,
            available=False,
            action="allow",
            allowed=True,
            risk_score=0.0,
            reasons=[f"agent_guard_unavailable: {exc}"],
            gateway_url=url,
        )

    return AgentToolGuardResult(
        tool=tool,
        arguments=arguments,
        enabled=True,
        available=True,
        action=str(data.get("action") or "block"),
        allowed=bool(data.get("allowed")),
        risk_score=float(data.get("risk_score") or 0.0),
        reasons=list(data.get("reasons") or []),
        danger_labels=list(data.get("danger_labels") or []),
        safe_arguments=data.get("safe_arguments"),
        gateway_url=url,
    )
