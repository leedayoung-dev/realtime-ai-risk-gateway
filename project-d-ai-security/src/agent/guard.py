"""Agent tool-call security guard."""

from __future__ import annotations

import json
import re
from typing import Any

from src.agent.policy import base_permission
from src.detection.engine import combined_risk, llm_judge_score, ml_score, rule_score
from src.dlp.scanner import scan
from src.models import (
    AgentGuardResponse,
    AgentToolCall,
    PolicyAction,
    ToolName,
)
from src.monitoring.store import record_agent_event
from src.policy.engine import decide

_DANGEROUS_ARG_PATTERNS: list[tuple[str, str, float]] = [
    (r"\brm\s+-rf\b", "destructive_shell", 95.0),
    (r"\bDROP\s+TABLE\b", "destructive_sql", 95.0),
    (r"\bDELETE\s+FROM\b", "destructive_sql", 90.0),
    (r"\bTRUNCATE\b", "destructive_sql", 90.0),
    (r"\.\./", "path_traversal", 85.0),
    (r"/etc/passwd", "sensitive_path", 90.0),
    (r"\bcurl\s+.*\|.*sh\b", "remote_code_exec", 95.0),
    (r"169\.254\.169\.254", "cloud_metadata", 92.0),
]


def _args_blob(arguments: dict[str, Any]) -> str:
    return json.dumps(arguments, ensure_ascii=False)


def _scan_dangerous_args(blob: str) -> tuple[float, list[str]]:
    score = 0.0
    labels: list[str] = []
    for pattern, label, hit in _DANGEROUS_ARG_PATTERNS:
        if re.search(pattern, blob, flags=re.IGNORECASE):
            labels.append(label)
            score = max(score, hit)
    return score, labels


def _stricter(a: PolicyAction, b: PolicyAction) -> PolicyAction:
    rank = {
        PolicyAction.ALLOW: 0,
        PolicyAction.MASK: 1,
        PolicyAction.REVIEW: 2,
        PolicyAction.BLOCK: 3,
    }
    return a if rank[a] >= rank[b] else b


def evaluate_tool_call(
    call: AgentToolCall,
    *,
    user_id: str = "agent",
    persist: bool = True,
) -> AgentGuardResponse:
    reasons: list[str] = []
    permission = base_permission(call.tool)
    reasons.append(f"tool_policy:{call.tool.value}={permission.value}")

    blob = _args_blob(call.arguments)
    danger_score, danger_labels = _scan_dangerous_args(blob)
    if danger_labels:
        reasons.extend(f"dangerous_arg:{x}" for x in danger_labels)

    findings = scan(blob)
    layers = [rule_score(blob), ml_score(blob), llm_judge_score(blob)]
    content_risk = combined_risk(layers)
    content_action, content_reasons = decide(content_risk, findings)
    reasons.extend(content_reasons)

    # Start from catalog permission, escalate on content/args risk
    action = permission
    if danger_score >= 85:
        action = _stricter(action, PolicyAction.BLOCK)
        reasons.append("dangerous_arguments_block")
    action = _stricter(action, content_action)

    # Tool-specific argument checks
    if call.tool == ToolName.DB_WRITE:
        action = PolicyAction.BLOCK
        reasons.append("db_write_denied")
    elif call.tool == ToolName.EXTERNAL_API:
        action = PolicyAction.BLOCK
        reasons.append("external_api_denied")
    elif call.tool == ToolName.FILE_WRITE:
        path = str(call.arguments.get("path", ""))
        if any(x in path for x in ("..", "/etc/", "C:\\Windows")):
            action = PolicyAction.BLOCK
            reasons.append("unsafe_file_path")

    risk = round(max(content_risk, danger_score), 1)
    if action == PolicyAction.BLOCK:
        risk = max(risk, 90.0)
    elif action == PolicyAction.REVIEW:
        risk = max(risk, 55.0)

    # ALLOW / MASK can execute (MASK uses redacted args); REVIEW / BLOCK cannot
    allowed = action in {PolicyAction.ALLOW, PolicyAction.MASK}

    safe_arguments = dict(call.arguments)
    if findings:
        text = blob
        for f in findings:
            if f.action == PolicyAction.MASK and isinstance(f.value, str):
                text = text.replace(f.value, f"[{f.kind.upper()}_MASKED]")
        try:
            safe_arguments = json.loads(text)
        except json.JSONDecodeError:
            safe_arguments = {"_redacted": True, "original_keys": list(call.arguments.keys())}

    response = AgentGuardResponse(
        call=call,
        action=action,
        allowed=allowed,
        risk_score=risk,
        reasons=reasons,
        danger_labels=danger_labels,
        dlp_findings=findings,
        safe_arguments=safe_arguments if action != PolicyAction.BLOCK else None,
    )

    if persist:
        record_agent_event(user_id, response)
    return response
