"""Security gateway orchestration (D-F-01, D-F-05)."""

from __future__ import annotations

from src.detection.engine import combined_risk, llm_judge_score, ml_score, rule_score
from src.dlp.scanner import mask_text, scan
from src.models import GuardResponse, InspectionResult, PolicyAction
from src.monitoring.store import record_guard
from src.policy.engine import decide


def inspect_text(text: str) -> InspectionResult:
    layers = [rule_score(text), ml_score(text), llm_judge_score(text)]
    risk = combined_risk(layers)
    findings = scan(text)
    action, reasons = decide(risk, findings)
    masked = mask_text(text, findings) if findings else text
    return InspectionResult(
        text=text,
        risk_score=risk,
        layers=layers,
        dlp_findings=findings,
        action=action,
        masked_text=masked if action in {PolicyAction.MASK, PolicyAction.ALLOW, PolicyAction.REVIEW} else None,
        reasons=reasons,
    )


def guard(user_id: str, prompt: str, output: str | None = None, *, persist: bool = True) -> GuardResponse:
    input_result = inspect_text(prompt)
    output_result = inspect_text(output) if output else None

    final_action = input_result.action
    if output_result and output_result.action == PolicyAction.BLOCK:
        final_action = PolicyAction.BLOCK
    elif (
        output_result
        and output_result.action == PolicyAction.MASK
        and final_action == PolicyAction.ALLOW
    ):
        final_action = PolicyAction.MASK

    safe_prompt = None
    safe_output = None
    if final_action in {PolicyAction.ALLOW, PolicyAction.MASK, PolicyAction.REVIEW}:
        safe_prompt = input_result.masked_text or prompt
    if output_result and final_action in {PolicyAction.ALLOW, PolicyAction.MASK}:
        safe_output = output_result.masked_text or output

    response = GuardResponse(
        input_inspection=input_result,
        output_inspection=output_result,
        final_action=final_action,
        safe_prompt=safe_prompt,
        safe_output=safe_output,
    )
    if persist:
        record_guard(user_id, response)
    return response
