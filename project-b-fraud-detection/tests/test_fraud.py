"""Project B feature / risk smoke tests."""

from __future__ import annotations

from src.features.engineering import build_features
from src.ingest.event_publisher import load_sample_users
from src.risk.service import compare_models


def test_build_features_from_samples() -> None:
    users = load_sample_users()
    assert users
    feats = build_features(users[0])
    assert feats["user_id"] == users[0].user_id
    assert "price_deviation" in feats
    assert "messages_per_5m" in feats


def test_compare_models_scores() -> None:
    users = load_sample_users()
    feats = build_features(users[0])
    cmp = compare_models(feats, persist=False)
    assert 0 <= cmp.supervised.risk_score <= 100
    assert 0 <= cmp.anomaly.risk_score <= 100
