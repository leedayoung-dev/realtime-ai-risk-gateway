"""Pull high-risk events from Project A/B dashboards."""

from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.insights.service import RiskInsightRequest, generate_insight
from src.insights.store import record_insight


def _label(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= settings.insight_risk_threshold:
        return "high"
    return "elevated"


def pull_from_news(threshold: float | None = None) -> list[dict[str, Any]]:
    thr = settings.insight_risk_threshold if threshold is None else threshold
    url = f"{settings.news_api_url.rstrip('/')}/v1/dashboard/overview"
    created: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=settings.insight_timeout_ms / 1000) as client:
            data = client.get(url).json()
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"news_pull_failed: {exc}"}]

    for row in data.get("articles") or []:
        score = float(row.get("risk_score") or 0)
        if score < thr:
            continue
        factors = row.get("factors") or {}
        signals = [f"{k}:{v}" for k, v in list(factors.items())[:6]]
        req = RiskInsightRequest(
            source="news",
            entity_id=str(row.get("article_id")),
            risk_score=score,
            label=_label(score),
            signals=signals,
            context={
                "title": row.get("title"),
                "source": row.get("source"),
            },
            user_id="pull-news",
        )
        insight = record_insight(generate_insight(req))
        created.append(insight.model_dump(mode="json"))
    return created


def pull_from_fraud(threshold: float | None = None) -> list[dict[str, Any]]:
    thr = settings.insight_risk_threshold if threshold is None else threshold
    url = f"{settings.fraud_api_url.rstrip('/')}/v1/dashboard/overview"
    created: list[dict[str, Any]] = []
    try:
        with httpx.Client(timeout=settings.insight_timeout_ms / 1000) as client:
            data = client.get(url).json()
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"fraud_pull_failed: {exc}"}]

    for row in data.get("users") or []:
        score = float(row.get("supervised_score") or 0)
        if score < thr:
            continue
        factors = row.get("factors") or {}
        signals = [f"{k}:{v}" for k, v in list(factors.items())[:6]]
        if row.get("agreement") is False:
            signals.append("model_disagreement")
        req = RiskInsightRequest(
            source="fraud",
            entity_id=str(row.get("user_id")),
            risk_score=score,
            label=_label(score),
            signals=signals,
            context={
                "user_id": row.get("user_id"),
                "label_hint": row.get("label_hint"),
                "anomaly_score": row.get("anomaly_score"),
                "delta": row.get("delta"),
            },
            user_id="pull-fraud",
        )
        insight = record_insight(generate_insight(req))
        created.append(insight.model_dump(mode="json"))
    return created


def pull_all(threshold: float | None = None) -> dict[str, Any]:
    news = pull_from_news(threshold=threshold)
    fraud = pull_from_fraud(threshold=threshold)
    news_ok = [x for x in news if "error" not in x]
    fraud_ok = [x for x in fraud if "error" not in x]
    return {
        "threshold": settings.insight_risk_threshold if threshold is None else threshold,
        "news_count": len(news_ok),
        "fraud_count": len(fraud_ok),
        "news": news,
        "fraud": fraud,
    }
