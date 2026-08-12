"""Agent tool permission catalog (D-F-15, D-F-16)."""

from __future__ import annotations

from src.models import PolicyAction, ToolName

# Default static policy from PRD / 초안
DEFAULT_TOOL_POLICY: dict[ToolName, PolicyAction] = {
    ToolName.SEARCH: PolicyAction.ALLOW,
    ToolName.DB_READ: PolicyAction.ALLOW,
    ToolName.DB_WRITE: PolicyAction.BLOCK,  # DENY → BLOCK
    ToolName.FILE_READ: PolicyAction.ALLOW,
    ToolName.FILE_WRITE: PolicyAction.REVIEW,
    ToolName.EMAIL: PolicyAction.REVIEW,
    ToolName.EXTERNAL_API: PolicyAction.BLOCK,  # DENY → BLOCK
}


def tool_policy_table() -> list[dict[str, str]]:
    return [
        {"tool": tool.value, "permission": action.value}
        for tool, action in DEFAULT_TOOL_POLICY.items()
    ]


def base_permission(tool: ToolName) -> PolicyAction:
    return DEFAULT_TOOL_POLICY.get(tool, PolicyAction.BLOCK)
