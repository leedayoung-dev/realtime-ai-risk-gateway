"""Push high-risk news events to Project C insights."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.models import ArticleAnalysis


def maybe_push_insight(analysis: ArticleAnalysis) -> dict[str, Any] | None:
    if not settings.insight_push_enabled:
        return None
    if analysis.risk.risk_score < settings.insight_push_threshold:
        return None

    signals = [f"{k}:{v}" for k, v in list(analysis.risk.factors.items())[:6]]
    payload = {
        "source": "news",
        "entity_id": analysis.article_id,
        "risk_score": analysis.risk.risk_score,
        "label": "critical" if analysis.risk.risk_score >= 80 else "high",
        "signals": signals,
        "context": {
            "title": analysis.title,
            "claim_count": analysis.risk.claim_count,
            "evidence_count": analysis.risk.evidence_count,
        },
        "user_id": "push-news",
    }
    url = f"{settings.llm_gateway_url.rstrip('/')}/v1/insights"
    try:
        with httpx.Client(timeout=settings.insight_push_timeout_ms / 1000) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return {"pushed": True, "status": resp.status_code}
    except Exception as exc:  # noqa: BLE001 — A must not fail if C is down
        return {"pushed": False, "error": str(exc)}
