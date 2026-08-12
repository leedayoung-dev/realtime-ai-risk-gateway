"""Fraud risk scorers — ML models with heuristic fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import settings
from src.models import FraudRisk
from src.risk.factors import explain_factors

logger = logging.getLogger(__name__)

FEATURE_KEYS = [
    "account_age_days",
    "transaction_count",
    "report_count",
    "listing_frequency",
    "price_deviation",
    "duplicate_listing_ratio",
    "messages_per_5m",
    "listing_burst",
    "new_users_contacted",
    "external_contact_attempt",
    "network_degree",
]

_SUPERVISED = None
_ANOMALY = None
_META = {"supervised_loaded": False, "anomaly_loaded": False}


def features_to_vector(features: dict[str, Any]) -> list[float]:
    return [float(features.get(k, 0.0)) for k in FEATURE_KEYS]


def _clip(score: float) -> float:
    return max(0.0, min(100.0, round(score, 1)))


def load_models() -> dict:
    global _SUPERVISED, _ANOMALY, _META
    import joblib

    sp = Path(settings.supervised_model_path)
    ap = Path(settings.anomaly_model_path)
    if sp.exists():
        _SUPERVISED = joblib.load(sp)
        _META["supervised_loaded"] = True
    if ap.exists():
        _ANOMALY = joblib.load(ap)
        _META["anomaly_loaded"] = True
    return dict(_META)


def model_status() -> dict:
    if not _META["supervised_loaded"] and settings.use_ml_model:
        load_models()
    return dict(_META)


def _heuristic_supervised(features: dict[str, float | int | str]) -> float:
    score = 10.0
    account_age = int(features["account_age_days"])
    if account_age < 7:
        score += 25
    elif account_age < 30:
        score += 10
    score += min(int(features["report_count"]) * 12, 24)
    score += min(float(features["price_deviation"]) * 40, 20)
    score += min(float(features["duplicate_listing_ratio"]) * 30, 15)
    score += min(int(features["messages_per_5m"]) * 1.2, 18)
    score += min(int(features["listing_burst"]) * 8, 16)
    score += min(int(features["external_contact_attempt"]) * 6, 12)
    score -= min(int(features["transaction_count"]) * 0.4, 10)
    return score


def score_supervised(features: dict[str, float | int | str]) -> FraudRisk:
    factors = explain_factors(features)
    heuristic = _heuristic_supervised(features)
    model_name = "supervised_heuristic"

    if settings.use_ml_model:
        if _SUPERVISED is None:
            load_models()
        if _SUPERVISED is not None:
            import numpy as np

            pred = float(_SUPERVISED.predict(np.array([features_to_vector(features)]))[0])
            score = 0.7 * pred + 0.3 * heuristic
            model_name = "supervised_gbr+heuristic"
            factors = {**factors, "model": model_name}
            return FraudRisk(
                user_id=str(features["user_id"]),
                risk_score=_clip(score),
                model=model_name,
                factors=factors,
            )

    factors = {**factors, "model": model_name}
    return FraudRisk(
        user_id=str(features["user_id"]),
        risk_score=_clip(heuristic),
        model=model_name,
        factors=factors,
    )


def score_anomaly(features: dict[str, float | int | str]) -> FraudRisk:
    factors = explain_factors(features)
    if settings.use_ml_model:
        if _ANOMALY is None:
            load_models()
        if _ANOMALY is not None:
            import numpy as np

            vec = np.array([features_to_vector(features)])
            # Lower score_samples => more anomalous
            sample_score = float(_ANOMALY.score_samples(vec)[0])
            # Map typical negative scores into 0~100 risk
            score = max(0.0, min(100.0, (-sample_score) * 140.0))
            model_name = "anomaly_isolation_forest"
            factors = {**factors, "model": model_name}
            return FraudRisk(
                user_id=str(features["user_id"]),
                risk_score=_clip(score),
                model=model_name,
                factors=factors,
            )

    baseline = {
        "account_age_days": 365.0,
        "transaction_count": 20.0,
        "report_count": 0.0,
        "listing_frequency": 2.0,
        "price_deviation": 0.1,
        "duplicate_listing_ratio": 0.0,
        "messages_per_5m": 4.0,
        "listing_burst": 0.0,
        "new_users_contacted": 2.0,
        "external_contact_attempt": 0.0,
        "network_degree": 3.0,
    }
    distance = 0.0
    for key in FEATURE_KEYS:
        value = float(features[key])
        ref = baseline[key]
        distance += abs(value - ref) / max(ref, 1.0)
    score = min(100.0, distance * 12)
    model_name = "anomaly_statistical"
    factors = {**factors, "model": model_name}
    return FraudRisk(
        user_id=str(features["user_id"]),
        risk_score=_clip(score),
        model=model_name,
        factors=factors,
    )
