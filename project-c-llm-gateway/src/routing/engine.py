"""Routing engine + fallback + optional Project D security gate."""

from __future__ import annotations

from src.analyzer.classifier import analyze_request
from src.config import settings
from src.evaluation.store import record
from src.models import ChatResponse, ModelName, RequestType, SecurityInfo
from src.providers.stub import invoke_model
from src.security.client import guard_prompt

_ROUTING: dict[RequestType, tuple[ModelName, ModelName]] = {
    RequestType.SIMPLE: (ModelName.GEMINI, ModelName.GPT),
    RequestType.COMPLEX_REASONING: (ModelName.CLAUDE, ModelName.GPT),
    RequestType.LONG_CONTEXT: (ModelName.GPT, ModelName.CLAUDE),
}


def routing_policy() -> dict[str, str]:
    return {
        RequestType.SIMPLE.value: f"{_ROUTING[RequestType.SIMPLE][0].value} → {_ROUTING[RequestType.SIMPLE][1].value}",
        RequestType.COMPLEX_REASONING.value: (
            f"{_ROUTING[RequestType.COMPLEX_REASONING][0].value} → {_ROUTING[RequestType.COMPLEX_REASONING][1].value}"
        ),
        RequestType.LONG_CONTEXT.value: (
            f"{_ROUTING[RequestType.LONG_CONTEXT][0].value} → {_ROUTING[RequestType.LONG_CONTEXT][1].value}"
        ),
    }


def route_chat(
    prompt: str,
    *,
    user_id: str = "anonymous",
    force_fallback: bool = False,
    simulate_primary_failure: bool = False,
    enable_security: bool | None = None,
    persist: bool = True,
) -> ChatResponse:
    request_type = analyze_request(prompt)
    primary, fallback = _ROUTING[request_type]

    use_security = settings.security_enabled if enable_security is None else enable_security
    security: SecurityInfo | None = None
    effective_prompt = prompt

    if use_security:
        security = guard_prompt(prompt, user_id=user_id)
        if security.available and security.final_action == "block":
            response = ChatResponse(
                request_type=request_type,
                primary_model=primary,
                used_model=primary,
                fallback_used=False,
                content="[blocked by AI Security Gateway] 요청이 보안 정책에 의해 차단되었습니다.",
                latency_ms=0,
                cost_usd=0.0,
                blocked=True,
                security=security,
            )
            if persist:
                record(response)
            return response
        if security.available and security.safe_prompt:
            effective_prompt = security.safe_prompt

    use_fallback = force_fallback or settings.gateway_force_fallback or simulate_primary_failure

    try:
        if use_fallback and simulate_primary_failure:
            raise TimeoutError("simulated primary failure")
        if use_fallback and force_fallback:
            raise TimeoutError("forced fallback")
        result = invoke_model(primary, effective_prompt, fail=False)
        response = ChatResponse(
            request_type=request_type,
            primary_model=primary,
            used_model=result.model,
            fallback_used=False,
            content=result.content,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            security=security,
        )
    except TimeoutError as exc:
        result = invoke_model(fallback, effective_prompt, fail=False)
        response = ChatResponse(
            request_type=request_type,
            primary_model=primary,
            used_model=result.model,
            fallback_used=True,
            fallback_reason=str(exc),
            content=result.content,
            latency_ms=result.latency_ms,
            cost_usd=result.cost_usd,
            security=security,
        )

    # Output guard (optional second hop to D)
    if use_security and security and security.available:
        out_sec = guard_prompt(effective_prompt, user_id=user_id, output=response.content)
        if out_sec.available and out_sec.final_action == "block":
            response.blocked = True
            response.content = "[blocked by AI Security Gateway] 모델 출력이 보안 정책에 의해 차단되었습니다."
            response.cost_usd = 0.0
            response.security = out_sec
        elif out_sec.available:
            if out_sec.safe_output:
                response.content = out_sec.safe_output
            # Keep stricter input decision (mask/review) visible in response metadata
            if security.final_action in {"mask", "review"}:
                security.safe_output = out_sec.safe_output or response.content
                response.security = security
            else:
                response.security = out_sec

    if persist:
        record(response)
    return response
