"""In-memory risk insight history."""

from __future__ import annotations

from threading import RLock

from src.insights.service import RiskInsight

_lock = RLock()
_HISTORY: list[RiskInsight] = []
_MAX = 100


def record_insight(insight: RiskInsight) -> RiskInsight:
    with _lock:
        _HISTORY.append(insight)
        if len(_HISTORY) > _MAX:
            del _HISTORY[:-_MAX]
    return insight


def list_insights(limit: int = 20) -> list[RiskInsight]:
    with _lock:
        return list(_HISTORY[-limit:])[::-1]


def clear_insights() -> None:
    with _lock:
        _HISTORY.clear()
