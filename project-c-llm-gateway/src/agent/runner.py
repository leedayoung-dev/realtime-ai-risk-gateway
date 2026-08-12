"""Agent loop: plan tools → D agent guard → stub execute → LLM answer."""

from __future__ import annotations

from src.agent.client_d import guard_tool_call
from src.agent.executor import execute_tool
from src.agent.planner import plan_tools
from src.config import settings
from src.models import AgentRunRequest, AgentRunResponse, AgentToolTrace
from src.routing.engine import route_chat
from src.agent.store import record_agent_run


def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    use_security = (
        settings.security_enabled if request.enable_security is None else request.enable_security
    )
    planned = plan_tools(request.prompt)
    traces: list[AgentToolTrace] = []
    tool_context_parts: list[str] = []

    for plan in planned:
        guard = None
        executed = False
        result = None
        status = "skipped"

        if use_security:
            guard = guard_tool_call(
                plan.tool,
                plan.arguments,
                user_id=request.user_id,
                call_id=plan.call_id,
            )
            if guard.available and not guard.allowed:
                status = "blocked" if guard.action == "block" else "review"
            elif guard.available and guard.allowed:
                args = guard.safe_arguments if guard.safe_arguments is not None else plan.arguments
                result = execute_tool(plan.tool, args)
                executed = True
                status = "executed"
            else:
                # fail-open
                result = execute_tool(plan.tool, plan.arguments)
                executed = True
                status = "executed_fail_open"
        else:
            result = execute_tool(plan.tool, plan.arguments)
            executed = True
            status = "executed_no_security"

        if executed and result is not None:
            tool_context_parts.append(f"[{plan.tool}] {result}")

        traces.append(
            AgentToolTrace(
                call_id=plan.call_id,
                tool=plan.tool,
                arguments=plan.arguments,
                rationale=plan.rationale,
                guard=guard,
                executed=executed,
                result=result,
                status=status,
            )
        )

    if tool_context_parts:
        final_prompt = (
            "다음 tool 실행 결과를 바탕으로 사용자 요청에 답하세요.\n"
            f"사용자: {request.prompt}\n"
            "Tool results:\n"
            + "\n".join(tool_context_parts)
        )
    else:
        blocked_notes = [
            f"{t.tool}:{t.status}" for t in traces if t.status in {"blocked", "review"}
        ]
        final_prompt = (
            f"사용자 요청: {request.prompt}\n"
            f"보안 정책으로 tool이 실행되지 않았습니다: {', '.join(blocked_notes) or 'none'}\n"
            "가능한 범위에서 안전하게 안내하세요."
        )

    chat = route_chat(
        final_prompt,
        user_id=request.user_id,
        enable_security=use_security,
        persist=True,
    )

    return record_agent_run(
        AgentRunResponse(
            prompt=request.prompt,
            traces=traces,
            chat=chat,
            tools_planned=len(planned),
            tools_executed=sum(1 for t in traces if t.executed),
            tools_blocked=sum(1 for t in traces if t.status == "blocked"),
            tools_review=sum(1 for t in traces if t.status == "review"),
        )
    )
