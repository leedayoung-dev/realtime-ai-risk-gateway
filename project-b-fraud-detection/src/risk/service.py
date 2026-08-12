"""Fraud risk orchestration."""

from __future__ import annotations

from src.features.store import put_features
from src.models import ModelComparison
from src.models_ml.scorers import score_anomaly, score_supervised


def compare_models(features: dict[str, float | int | str], persist: bool = True) -> ModelComparison:
    if persist and "user_id" in features:
        put_features(str(features["user_id"]), features)
    supervised = score_supervised(features)
    anomaly = score_anomaly(features)
    delta = abs(supervised.risk_score - anomaly.risk_score)
    agreement = delta <= 15
    return ModelComparison(
        user_id=str(features["user_id"]),
        supervised=supervised,
        anomaly=anomaly,
        agreement=agreement,
        delta=round(delta, 1),
    )
