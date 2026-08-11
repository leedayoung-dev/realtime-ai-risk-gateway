"""Credibility risk scoring skeleton (A-F-10, A-F-11)."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models import CredibilityRisk


def score_risk(features: dict[str, float | int | str]) -> CredibilityRisk:
    """Heuristic risk score for M1 local demos.

    M3 will replace this with trained ML/NLP models and temporal updates.
    """
    claim_count = int(features.get("claim_count", 0))
    contradicting = int(features.get("evidence_contradicting", 0))
    official = int(features.get("evidence_official", 0))
    content_length = int(features.get("content_length", 0))

    score = 20.0
    score += min(claim_count * 8, 24)
    score += min(contradicting * 10, 30)
    score -= min(official * 5, 15)
    if content_length < 80:
        score += 10
    score = max(0.0, min(100.0, score))

    factors: dict[str, str] = {}
    if contradicting > 0:
        factors["contradicting_evidence"] = "HIGH"
    if claim_count >= 2:
        factors["multi_claim"] = "MEDIUM"
    if content_length < 80:
        factors["thin_content"] = "MEDIUM"
    if not factors:
        factors["baseline"] = "LOW"

    return CredibilityRisk(
        article_id=str(features["article_id"]),
        risk_score=round(score, 1),
        updated_at=datetime.now(timezone.utc),
        factors=factors,
    )
