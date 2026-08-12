"""Train supervised regressor + IsolationForest anomaly model."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error

from src.config import settings
from src.features.engineering import build_features
from src.ingest.event_publisher import load_sample_users
from src.models_ml.scorers import FEATURE_KEYS, features_to_vector

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("train_fraud_models")


def _rows():
    labels = json.loads(Path(settings.training_data_path).read_text(encoding="utf-8"))["samples"]
    users = {u.user_id: u for u in load_sample_users()}
    x, y_risk, y_cls, ids = [], [], [], []
    for row in labels:
        if "features" in row:
            feats = dict(row["features"])
            feats["user_id"] = row["user_id"]
        else:
            user = users.get(row["user_id"])
            if user is None:
                continue
            feats = build_features(user)
        x.append(features_to_vector(feats))
        y_risk.append(float(row["label_risk"]))
        y_cls.append(int(row["label"]))
        ids.append(row["user_id"])
    return np.array(x), np.array(y_risk), np.array(y_cls), ids


def train() -> dict:
    x, y_risk, y_cls, ids = _rows()
    if len(x) < 6:
        raise RuntimeError("Need at least 6 labeled samples")

    supervised = GradientBoostingRegressor(
        random_state=42, n_estimators=80, max_depth=2, learning_rate=0.08
    )
    supervised.fit(x, y_risk)
    pred = supervised.predict(x)
    mae = float(mean_absolute_error(y_risk, pred))

    # Fit anomaly model primarily on low-risk samples
    normal = x[y_cls == 0] if (y_cls == 0).any() else x
    anomaly = IsolationForest(random_state=42, contamination=0.35, n_estimators=100)
    anomaly.fit(normal)

    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)
    supervised_path = Path(settings.supervised_model_path)
    anomaly_path = Path(settings.anomaly_model_path)
    joblib.dump(supervised, supervised_path)
    joblib.dump(anomaly, anomaly_path)

    report = {
        "n_samples": len(ids),
        "samples": ids,
        "supervised_mae_train": round(mae, 3),
        "supervised_model_path": str(supervised_path),
        "anomaly_model_path": str(anomaly_path),
        "feature_keys": FEATURE_KEYS,
    }
    Path("artifacts/train_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Trained models MAE=%.3f n=%s", mae, len(ids))
    return report


if __name__ == "__main__":
    print(json.dumps(train(), ensure_ascii=False, indent=2))
