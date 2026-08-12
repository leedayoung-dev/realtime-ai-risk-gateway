"""Early Detection evaluation (PRD success metric).

Measures whether high-risk articles are flagged before official fact-check time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from src.collector.news_collector import load_sample_articles
from src.pipeline.analyze import analyze_article


class EarlyDetectionCase(BaseModel):
    article_id: str
    needs_verification: bool
    published_at: datetime
    factcheck_at: datetime | None = None
    detection_threshold: float = 50


class CaseResult(BaseModel):
    article_id: str
    needs_verification: bool
    risk_score: float
    predicted_positive: bool
    true_positive: bool
    false_positive: bool
    false_negative: bool
    true_negative: bool
    early_detected: bool | None = None
    lead_time_minutes: float | None = None


class EarlyDetectionReport(BaseModel):
    threshold: float
    n_cases: int
    precision: float
    recall: float
    false_positive_rate: float
    early_detection_rate: float
    avg_lead_time_minutes: float | None = None
    cases: list[CaseResult] = Field(default_factory=list)


def _load_cases(path: str = "data/samples/early_detection_cases.json") -> list[EarlyDetectionCase]:
    with Path(path).open(encoding="utf-8") as f:
        payload = json.load(f)
    return [EarlyDetectionCase.model_validate(item) for item in payload["cases"]]


def evaluate_early_detection(
    threshold: float = 50.0,
    cases_path: str = "data/samples/early_detection_cases.json",
) -> EarlyDetectionReport:
    cases = _load_cases(cases_path)
    articles = {a.article_id: a for a in load_sample_articles()}
    results: list[CaseResult] = []

    tp = fp = fn = tn = 0
    early_hits = 0
    early_eligible = 0
    lead_times: list[float] = []

    now = datetime.now(timezone.utc)

    for case in cases:
        article = articles.get(case.article_id)
        if article is None:
            continue
        analysis = analyze_article(article, persist_features=True)
        score = analysis.risk.risk_score
        predicted = score >= threshold

        true_positive = predicted and case.needs_verification
        false_positive = predicted and not case.needs_verification
        false_negative = (not predicted) and case.needs_verification
        true_negative = (not predicted) and not case.needs_verification

        tp += int(true_positive)
        fp += int(false_positive)
        fn += int(false_negative)
        tn += int(true_negative)

        early = None
        lead = None
        if case.needs_verification and case.factcheck_at is not None:
            early_eligible += 1
            # Detection is considered "now" relative to factcheck timestamp in the scenario.
            detected_at = now if predicted else None
            if predicted:
                # Use published_at as proxy detection time for offline eval consistency
                detected_at = case.published_at
                lead = (case.factcheck_at - detected_at).total_seconds() / 60.0
                early = lead > 0
                if early:
                    early_hits += 1
                    lead_times.append(lead)
            else:
                early = False

        results.append(
            CaseResult(
                article_id=case.article_id,
                needs_verification=case.needs_verification,
                risk_score=score,
                predicted_positive=predicted,
                true_positive=true_positive,
                false_positive=false_positive,
                false_negative=false_negative,
                true_negative=true_negative,
                early_detected=early,
                lead_time_minutes=None if lead is None else round(lead, 1),
            )
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    early_rate = early_hits / early_eligible if early_eligible else 0.0
    avg_lead = sum(lead_times) / len(lead_times) if lead_times else None

    return EarlyDetectionReport(
        threshold=threshold,
        n_cases=len(results),
        precision=round(precision, 3),
        recall=round(recall, 3),
        false_positive_rate=round(fpr, 3),
        early_detection_rate=round(early_rate, 3),
        avg_lead_time_minutes=None if avg_lead is None else round(avg_lead, 1),
        cases=results,
    )
