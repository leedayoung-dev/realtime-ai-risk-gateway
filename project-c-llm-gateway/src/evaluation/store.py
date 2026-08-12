"""In-memory analytics for routed requests."""

from __future__ import annotations

from threading import RLock

from src.models import ChatResponse

_lock = RLock()
_HISTORY: list[ChatResponse] = []
_MAX = 200


def record(response: ChatResponse) -> ChatResponse:
    with _lock:
        _HISTORY.append(response)
        if len(_HISTORY) > _MAX:
            del _HISTORY[:-_MAX]
    return response


def list_history(limit: int = 50) -> list[ChatResponse]:
    with _lock:
        return list(_HISTORY[-limit:])[::-1]


def clear_history() -> None:
    with _lock:
        _HISTORY.clear()


def aggregate() -> dict:
    with _lock:
        items = list(_HISTORY)

    total = len(items)
    if total == 0:
        return {
            "request_count": 0,
            "fallback_rate": 0.0,
            "avg_latency_ms": 0.0,
            "total_cost_usd": 0.0,
            "by_request_type": {},
            "by_model": {},
            "fallback_count": 0,
        }

    fallback_count = sum(1 for x in items if x.fallback_used)
    by_type: dict[str, int] = {}
    by_model: dict[str, dict[str, float | int]] = {}

    for item in items:
        by_type[item.request_type.value] = by_type.get(item.request_type.value, 0) + 1
        bucket = by_model.setdefault(
            item.used_model.value,
            {"count": 0, "cost_usd": 0.0, "latency_ms_sum": 0},
        )
        bucket["count"] = int(bucket["count"]) + 1
        bucket["cost_usd"] = float(bucket["cost_usd"]) + item.cost_usd
        bucket["latency_ms_sum"] = int(bucket["latency_ms_sum"]) + item.latency_ms

    model_stats = {}
    for name, bucket in by_model.items():
        count = int(bucket["count"])
        model_stats[name] = {
            "count": count,
            "cost_usd": round(float(bucket["cost_usd"]), 4),
            "avg_latency_ms": round(int(bucket["latency_ms_sum"]) / count, 1),
        }

    return {
        "request_count": total,
        "fallback_count": fallback_count,
        "fallback_rate": round(fallback_count / total, 3),
        "avg_latency_ms": round(sum(x.latency_ms for x in items) / total, 1),
        "total_cost_usd": round(sum(x.cost_usd for x in items), 4),
        "by_request_type": by_type,
        "by_model": model_stats,
    }


def seed_demo_traffic() -> int:
    """Run a few canned routes so dashboard is not empty on first load."""
    from src.routing.engine import route_chat

    demos = [
        ("오늘 서울 날씨 한 줄로 알려줘", False, False),
        (
            "실시간 사기 탐지에서 supervised와 anomaly detection 비교 실험 설계를 단계별로 설명해줘. 근거 포함.",
            False,
            False,
        ),
        ("다음 문서를 요약해줘. " + ("본문 " * 40), False, False),
        ("간단한 번역: hello", True, False),
        (
            "아키텍처 비교 분석이 필요해. 왜 이 라우팅이 맞는지 근거를 들어 설명해.",
            False,
            True,
        ),
    ]
    for prompt, force_fb, sim_fail in demos:
        route_chat(
            prompt,
            force_fallback=force_fb,
            simulate_primary_failure=sim_fail,
            enable_security=False,
        )
    return len(demos)
