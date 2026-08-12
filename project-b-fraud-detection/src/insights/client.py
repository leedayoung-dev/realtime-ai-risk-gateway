"""Push high-risk fraud events to Project C insights."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.models import ModelComparison


def maybe_push_insight(comparison: ModelComparison, *, user_id: str, label_hint: str | None = None) -> dict[str, Any] | None:
    if not settings.insight_push_enabled:
        return None
    score = comparison.supervised.risk_score
    if score < settings.insight_push_threshold:
        return None

    factors = comparison.supervised.factors or {}
    signals = [f"{k}:{v}" for k, v in list(factors.items())[:6]]
    if not comparison.agreement:
        signals.append("model_disagreement")

    payload = {
        "source": "fraud",
        "entity_id": user_id,
        "risk_score": score,
        "label": "critical" if score >= 80 else "high",
        "signals": signals,
        "context": {
            "user_id": user_id,
            "label_hint": label_hint,
            "anomaly_score": comparison.anomaly.risk_score,
            "delta": comparison.delta,
            "agreement": comparison.agreement,
        },
        "user_id": "push-fraud",
    }
    url = f"{settings.llm_gateway_url.rstrip('/')}/v1/insights"
    try:
        with httpx.Client(timeout=settings.insight_push_timeout_ms / 1000) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return {"pushed": True, "status": resp.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": False, "error": str(exc)}
