"""FastAPI fraud risk API — M2/M3 with dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from src.evaluation.compare import EvalReport, evaluate_models
from src.features.engineering import build_features
from src.features.store import get_features as get_stored_features
from src.ingest.event_publisher import load_sample_users
from src.insights.client import maybe_push_insight
from src.models import FraudRisk, ModelComparison
from src.models_ml.scorers import model_status, score_supervised
from src.risk.service import compare_models

app = FastAPI(
    title="Fraud Detection API",
    version="0.3.0",
    description="Real-time fraud risk (Project B, M2/M3)",
)

_DASHBOARD = Path(__file__).resolve().parent / "static" / "dashboard.html"
_USERS = {u.user_id: u for u in load_sample_users()}


@app.on_event("startup")
def _startup() -> None:
    model_status()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.3.0", "model": model_status(), "user_count": len(_USERS)}


@app.get("/v1/users")
def list_users() -> list[dict]:
    return [{"user_id": u.user_id, "label_hint": u.label_hint} for u in _USERS.values()]


@app.get("/v1/users/{user_id}/features")
def get_features(user_id: str) -> dict:
    user = _USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    cached = get_stored_features(user_id)
    if cached is not None:
        return {"source": "feature_store", "features": cached}
    feats = build_features(user)
    compare_models(feats, persist=True)
    return {"source": "computed", "features": feats}


@app.get("/v1/users/{user_id}/risk", response_model=FraudRisk)
def get_risk(user_id: str) -> FraudRisk:
    user = _USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    feats = build_features(user)
    compare_models(feats, persist=True)
    return score_supervised(feats)


@app.get("/v1/users/{user_id}/compare", response_model=ModelComparison)
def compare_risk(user_id: str) -> ModelComparison:
    user = _USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    result = compare_models(build_features(user), persist=True)
    maybe_push_insight(result, user_id=user_id, label_hint=user.label_hint)
    return result


@app.get("/v1/evaluation/compare", response_model=EvalReport)
def eval_compare(threshold: float = 50.0) -> EvalReport:
    return evaluate_models(threshold=threshold)


@app.get("/v1/model")
def get_model() -> dict:
    return model_status()


@app.get("/v1/dashboard/overview")
def overview() -> dict:
    users = []
    supervised_scores = []
    agreements = 0
    for user in _USERS.values():
        cmp = compare_models(build_features(user), persist=True)
        supervised_scores.append(cmp.supervised.risk_score)
        agreements += int(cmp.agreement)
        users.append(
            {
                "user_id": user.user_id,
                "label_hint": user.label_hint,
                "supervised_score": cmp.supervised.risk_score,
                "anomaly_score": cmp.anomaly.risk_score,
                "delta": cmp.delta,
                "agreement": cmp.agreement,
                "factors": cmp.supervised.factors,
            }
        )
    n = len(users) or 1
    return {
        "user_count": len(users),
        "avg_supervised": round(sum(supervised_scores) / n, 2),
        "agreement_rate": round(agreements / n, 3),
        "model": model_status(),
        "users": users,
    }
