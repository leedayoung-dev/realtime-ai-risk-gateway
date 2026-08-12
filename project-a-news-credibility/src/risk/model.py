"""Trainable credibility risk model (A-F-10)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)

FEATURE_KEYS = [
    "claim_count",
    "avg_claim_confidence",
    "evidence_supporting",
    "evidence_contradicting",
    "evidence_official",
    "evidence_matched",
    "avg_evidence_relevance",
    "content_length",
    "source_trust",
    "share_velocity",
    "share_acceleration",
    "burst",
    "engagement_pattern",
]

_MODEL = None
_MODEL_META: dict[str, Any] = {"loaded": False, "path": None, "backend": "heuristic"}


def features_to_vector(features: dict[str, Any]) -> list[float]:
    return [float(features.get(k, 0.0)) for k in FEATURE_KEYS]


def load_model(path: str | None = None):
    global _MODEL, _MODEL_META
    model_path = Path(path or settings.model_path)
    if not model_path.exists():
        _MODEL = None
        _MODEL_META = {"loaded": False, "path": str(model_path), "backend": "heuristic"}
        return None
    import joblib

    _MODEL = joblib.load(model_path)
    _MODEL_META = {"loaded": True, "path": str(model_path), "backend": "sklearn_gbr"}
    logger.info("Loaded risk model from %s", model_path)
    return _MODEL


def model_status() -> dict[str, Any]:
    if _MODEL is None and settings.use_ml_model:
        load_model()
    return dict(_MODEL_META)


def predict_ml_score(features: dict[str, Any]) -> float | None:
    if not settings.use_ml_model:
        return None
    model = _MODEL
    if model is None:
        model = load_model()
    if model is None:
        return None
    import numpy as np

    vec = np.array([features_to_vector(features)])
    pred = float(model.predict(vec)[0])
    return max(0.0, min(100.0, pred))
