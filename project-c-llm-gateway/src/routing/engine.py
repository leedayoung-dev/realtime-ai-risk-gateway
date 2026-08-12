"""Routing engine + fallback (C-F-03, C-F-04)."""

from __future__ import annotations

from src.analyzer.classifier import analyze_request
from src.config import settings
from src.models import ChatResponse, ModelName, RequestType
from src.providers.stub import invoke_model

_ROUTING: dict[RequestType, tuple[ModelName, ModelName]] = {
    RequestType.SIMPLE: (ModelName.GEMINI, ModelName.GPT),
    RequestType.COMPLEX_REASONING: (ModelName.CLAUDE, ModelName.GPT),
    RequestType.LONG_CONTEXT: (ModelName.GPT, ModelName.CLAUDE),
}


def route_chat(
    prompt: str,
    *,
    force_fallback: bool = False,
    simulate_primary_failure: bool = False,
) -> ChatResponse:
    request_type = analyze_request(prompt)
    primary, fallback = _ROUTING[request_type]
    use_fallback = force_fallback or settings.gateway_force_fallback or simulate_primary_failure
    reason: str | None = None

    try:
        if use_fallback and simulate_primary_failure:
            raise TimeoutError("simulated primary failure")
        if use_fallback and force_fallback:
            raise TimeoutError("forced fallback")
        result = invoke_model(primary, prompt, fail=False)
        return ChatResponse(
            request_type=request_type,
            primary_model=primary,
            used_model=result.model,
            fallback_used=False,
            content=result.content,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
        )
    except TimeoutError as exc:
        reason = str(exc)
        result = invoke_model(fallback, prompt, fail=False)
        return ChatResponse(
            request_type=request_type,
            primary_model=primary,
            used_model=result.model,
            fallback_used=True,
            fallback_reason=reason,
            content=result.content,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
        )
