"""Compare supervised vs anomaly detection on labeled samples."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.config import settings
from src.features.engineering import build_features
from src.ingest.event_publisher import load_sample_users
from src.risk.service import compare_models


class EvalCase(BaseModel):
    user_id: str
    label: int
    supervised_score: float
    anomaly_score: float
    supervised_pred: int
    anomaly_pred: int
    agreement: bool


class EvalReport(BaseModel):
    threshold: float
    n_cases: int
    supervised_precision: float
    supervised_recall: float
    anomaly_precision: float
    anomaly_recall: float
    agreement_rate: float
    cases: list[EvalCase] = Field(default_factory=list)


def _metrics(y_true: list[int], y_pred: list[int]) -> tuple[float, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return round(precision, 3), round(recall, 3)


def evaluate_models(threshold: float = 50.0) -> EvalReport:
    labels = json.loads(Path(settings.training_data_path).read_text(encoding="utf-8"))["samples"]
    users = {u.user_id: u for u in load_sample_users()}
    cases: list[EvalCase] = []
    y_true: list[int] = []
    y_sup: list[int] = []
    y_ano: list[int] = []

    for row in labels:
        user_id = row["user_id"]
        if "features" in row:
            feats = dict(row["features"])
            feats["user_id"] = user_id
        else:
            user = users.get(user_id)
            if user is None:
                continue
            feats = build_features(user)

        cmp = compare_models(feats)
        label = int(row["label"])
        s_pred = int(cmp.supervised.risk_score >= threshold)
        a_pred = int(cmp.anomaly.risk_score >= threshold)
        y_true.append(label)
        y_sup.append(s_pred)
        y_ano.append(a_pred)
        cases.append(
            EvalCase(
                user_id=user_id,
                label=label,
                supervised_score=cmp.supervised.risk_score,
                anomaly_score=cmp.anomaly.risk_score,
                supervised_pred=s_pred,
                anomaly_pred=a_pred,
                agreement=cmp.agreement,
            )
        )

    sp, sr = _metrics(y_true, y_sup)
    ap, ar = _metrics(y_true, y_ano)
    agree = sum(1 for c in cases if c.agreement) / len(cases) if cases else 0.0
    return EvalReport(
        threshold=threshold,
        n_cases=len(cases),
        supervised_precision=sp,
        supervised_recall=sr,
        anomaly_precision=ap,
        anomaly_recall=ar,
        agreement_rate=round(agree, 3),
        cases=cases,
    )
