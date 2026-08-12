"""In-memory agent run history for dashboard."""

from __future__ import annotations

from threading import RLock

from src.models import AgentRunResponse

_lock = RLock()
_HISTORY: list[AgentRunResponse] = []
_MAX = 100


def record_agent_run(response: AgentRunResponse) -> AgentRunResponse:
    with _lock:
        _HISTORY.append(response)
        if len(_HISTORY) > _MAX:
            del _HISTORY[:-_MAX]
    return response


def list_agent_runs(limit: int = 20) -> list[AgentRunResponse]:
    with _lock:
        return list(_HISTORY[-limit:])[::-1]
