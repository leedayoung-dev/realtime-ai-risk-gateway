"""Train GradientBoosting risk model from labeled samples."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.claims.extractor import extract_claims
from src.collector.news_collector import load_sample_articles
from src.config import settings
from src.evidence.retriever import retrieve_evidence
from src.features.engineering import build_features
from src.risk.model import FEATURE_KEYS, features_to_vector

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("train_risk_model")


def _load_labels(path: str) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return list(json.load(f)["samples"])


def build_training_matrix(label_path: str | None = None):
    labels = _load_labels(label_path or settings.training_data_path)
    articles = {a.article_id: a for a in load_sample_articles()}

    x_rows: list[list[float]] = []
    y_rows: list[float] = []
    used: list[str] = []

    for row in labels:
        article_id = row["article_id"]
        if "features" in row:
            features = row["features"]
            features["article_id"] = article_id
        else:
            article = articles.get(article_id)
            if article is None:
                logger.warning("Skip missing article %s", article_id)
                continue
            claims = extract_claims(article)
            evidence = [ev for c in claims for ev in retrieve_evidence(c)]
            features = build_features(article, claims, evidence)

        x_rows.append(features_to_vector(features))
        y_rows.append(float(row["label_risk"]))
        used.append(article_id)

    return x_rows, y_rows, used


def train_and_save(output_path: str | None = None) -> dict:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    import joblib
    import numpy as np

    x_rows, y_rows, used = build_training_matrix()
    if len(x_rows) < 4:
        raise RuntimeError("Need at least 4 labeled samples to train")

    x = np.array(x_rows)
    y = np.array(y_rows)

    model = GradientBoostingRegressor(
        random_state=42,
        n_estimators=80,
        max_depth=2,
        learning_rate=0.08,
    )
    model.fit(x, y)
    pred = model.predict(x)
    mae = float(mean_absolute_error(y, pred))

    out = Path(output_path or settings.model_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out)

    report = {
        "model_path": str(out),
        "n_samples": len(used),
        "feature_keys": FEATURE_KEYS,
        "mae_train": round(mae, 3),
        "samples": used,
    }
    report_path = out.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved model to %s (MAE=%.3f, n=%s)", out, mae, len(used))
    return report


if __name__ == "__main__":
    print(json.dumps(train_and_save(), ensure_ascii=False, indent=2))
