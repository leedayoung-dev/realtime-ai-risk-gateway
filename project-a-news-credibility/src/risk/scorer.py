"""Credibility risk scoring + temporal history (A-F-10, A-F-11)."""

from __future__ import annotations

from datetime import datetime, timezone

from src.models import CredibilityRisk, RiskHistoryPoint
from src.risk.model import model_status, predict_ml_score

_HISTORY: dict[str, list[RiskHistoryPoint]] = {}


def _heuristic_score(features: dict[str, float | int | str]) -> tuple[float, dict[str, str]]:
    claim_count = int(features.get("claim_count", 0))
    contradicting = int(features.get("evidence_contradicting", 0))
    official = int(features.get("evidence_official", 0))
    supporting = int(features.get("evidence_supporting", 0))
    matched = int(features.get("evidence_matched", 0))
    source_trust = float(features.get("source_trust", 0.5))
    avg_rel = float(features.get("avg_evidence_relevance", 0.0))
    content_length = int(features.get("content_length", 0))
    burst = float(features.get("burst", 0.0))
    velocity = float(features.get("share_velocity", 0.0))

    score = 25.0
    score += min(claim_count * 6, 18)
    score += min(contradicting * 14, 28)
    score -= min(official * 8, 20)
    score -= min(supporting * 3, 9)
    score -= source_trust * 15
    score -= avg_rel * 8
    if matched == 0:
        score += 12
    if content_length < 80:
        score += 8
    score += min(velocity * 0.08, 10)
    if burst >= 1:
        score += 6

    article_id = str(features["article_id"])
    prior = _HISTORY.get(article_id, [])
    if prior and contradicting > 0:
        score += min(len(prior) * 2.5, 10)

    score = max(0.0, min(100.0, score))

    factors: dict[str, str] = {}
    if contradicting > 0:
        factors["contradicting_evidence"] = "HIGH"
    if official == 0:
        factors["missing_official_evidence"] = "MEDIUM"
    if source_trust < 0.5:
        factors["low_source_trust"] = "MEDIUM"
    if burst >= 1 or velocity >= 50:
        factors["propagation_priority"] = "HIGH"
    if claim_count >= 2:
        factors["multi_claim"] = "MEDIUM"
    if matched == 0:
        factors["evidence_gap"] = "HIGH"
    if not factors:
        factors["baseline"] = "LOW"
    return score, factors


def explain_factors(features: dict[str, float | int | str]) -> dict[str, str]:
    _, factors = _heuristic_score(features)
    return factors


def score_risk(features: dict[str, float | int | str]) -> CredibilityRisk:
    claim_count = int(features.get("claim_count", 0))
    matched = int(features.get("evidence_matched", 0))
    article_id = str(features["article_id"])

    ml_score = predict_ml_score(features)
    heuristic, factors = _heuristic_score(features)

    if ml_score is None:
        score = heuristic
        factors = {**factors, "model": "heuristic"}
    else:
        # Blend for stability on tiny datasets
        score = 0.65 * ml_score + 0.35 * heuristic
        factors = {**factors, "model": "ml+heuristic"}
        status = model_status()
        if status.get("loaded"):
            factors["model_backend"] = str(status.get("backend"))

    # Temporal drift still applies on final score
    prior = _HISTORY.get(article_id, [])
    if prior and int(features.get("evidence_contradicting", 0)) > 0:
        score = min(100.0, score + min(len(prior) * 1.5, 8))

    risk = CredibilityRisk(
        article_id=article_id,
        risk_score=round(max(0.0, min(100.0, score)), 1),
        updated_at=datetime.now(timezone.utc),
        factors=factors,
        claim_count=claim_count,
        evidence_count=matched,
    )
    _append_history(risk)
    return risk


def _append_history(risk: CredibilityRisk) -> None:
    point = RiskHistoryPoint(
        article_id=risk.article_id,
        risk_score=risk.risk_score,
        updated_at=risk.updated_at,
        factors=risk.factors,
    )
    bucket = _HISTORY.setdefault(risk.article_id, [])
    bucket.append(point)
    if len(bucket) > 20:
        del bucket[:-20]


def get_risk_history(article_id: str) -> list[RiskHistoryPoint]:
    return list(_HISTORY.get(article_id, []))


def clear_history(article_id: str | None = None) -> None:
    if article_id is None:
        _HISTORY.clear()
    else:
        _HISTORY.pop(article_id, None)
