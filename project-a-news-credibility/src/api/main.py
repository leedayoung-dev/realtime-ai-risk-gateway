"""FastAPI — M4+ realtime collect/stream integration."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.collector.news_collector import load_sample_articles, publish_articles
from src.collector.rss_collector import collect_news
from src.evaluation.early_detection import EarlyDetectionReport, evaluate_early_detection
from src.features.store import get_features, list_feature_keys
from src.insights.client import maybe_push_insight
from src.models import Article, ArticleAnalysis, Claim, CredibilityRisk, Evidence, RiskHistoryPoint
from src.pipeline.analyze import analyze_article
from src.risk.model import model_status
from src.risk.scorer import get_risk_history
from src.store.registry import get_article, list_articles, list_analyses, save_analysis
from src.streaming.bus import pending_local
from src.streaming.pipeline import run_local_batch

app = FastAPI(
    title="News Credibility API",
    version="0.5.0",
    description="Real-time news credibility risk (Project A, collect+stream)",
)

_DASHBOARD = Path(__file__).resolve().parent / "static" / "dashboard.html"


class CollectRequest(BaseModel):
    use_fixture: bool = True
    feed_url: str | None = None
    max_items: int = Field(default=8, ge=1, le=50)
    run_pipeline: bool = True


@app.on_event("startup")
def _startup() -> None:
    model_status()
    # seed registry
    list_articles()


@app.get("/")
def root_dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": "0.5.0",
        "model": model_status(),
        "pending_events": pending_local(),
        "article_count": len(list_articles()),
    }


@app.get("/v1/articles", response_model=list[Article])
def api_list_articles() -> list[Article]:
    return list_articles()


@app.get("/v1/articles/{article_id}", response_model=Article)
def api_get_article(article_id: str) -> Article:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return article


@app.get("/v1/articles/{article_id}/claims", response_model=list[Claim])
def get_claims(article_id: str) -> list[Claim]:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return analyze_article(article).claims


@app.get("/v1/articles/{article_id}/evidence", response_model=list[Evidence])
def get_evidence(article_id: str) -> list[Evidence]:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return analyze_article(article).evidence


@app.get("/v1/articles/{article_id}/features")
def get_article_features(article_id: str) -> dict:
    if get_article(article_id) is None:
        raise HTTPException(status_code=404, detail="article not found")
    cached = get_features(article_id)
    if cached is not None:
        return {"source": "feature_store", "features": cached}
    analysis = analyze_article(get_article(article_id))  # type: ignore[arg-type]
    cached = get_features(article_id) or {}
    return {"source": "computed", "features": cached, "risk_score": analysis.risk.risk_score}


@app.get("/v1/features")
def api_list_features() -> dict:
    return {"article_ids": list_feature_keys()}


@app.get("/v1/articles/{article_id}/risk", response_model=CredibilityRisk)
def get_risk(article_id: str) -> CredibilityRisk:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return analyze_article(article).risk


@app.get("/v1/articles/{article_id}/risk/history", response_model=list[RiskHistoryPoint])
def risk_history(article_id: str) -> list[RiskHistoryPoint]:
    if get_article(article_id) is None:
        raise HTTPException(status_code=404, detail="article not found")
    if not get_risk_history(article_id):
        analyze_article(get_article(article_id))  # type: ignore[arg-type]
    return get_risk_history(article_id)


@app.post("/v1/articles/{article_id}/analyze", response_model=ArticleAnalysis)
def analyze(article_id: str) -> ArticleAnalysis:
    article = get_article(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    analysis = analyze_article(article)
    save_analysis(analysis)
    maybe_push_insight(analysis)
    return analysis


@app.get("/v1/model")
def get_model() -> dict:
    return model_status()


@app.get("/v1/evaluation/early-detection", response_model=EarlyDetectionReport)
def early_detection(threshold: float = 50.0) -> EarlyDetectionReport:
    return evaluate_early_detection(threshold=threshold)


@app.post("/v1/collect/samples")
def collect_samples(run_pipeline: bool = True) -> dict:
    articles = load_sample_articles()
    bus = publish_articles(articles)
    pipeline = run_local_batch() if run_pipeline else {"processed": 0, "results": []}
    return {"collected": len(articles), "bus": bus, "pipeline": pipeline}


@app.post("/v1/collect/rss")
def collect_rss(request: CollectRequest) -> dict:
    result = collect_news(
        use_fixture=request.use_fixture,
        feed_url=request.feed_url,
        max_items=request.max_items,
        publish=True,
    )
    pipeline = run_local_batch() if request.run_pipeline else {"processed": 0, "results": []}
    return {**result, "pipeline": pipeline}


@app.post("/v1/pipeline/run")
def pipeline_run(max_messages: int | None = None) -> dict:
    return run_local_batch(max_messages=max_messages)


@app.get("/v1/pipeline/status")
def pipeline_status() -> dict:
    return {
        "pending_events": pending_local(),
        "article_count": len(list_articles()),
        "analysis_count": len(list_analyses()),
    }


@app.get("/v1/dashboard/overview")
def dashboard_overview() -> dict:
    articles_out = []
    scores: list[float] = []
    for article in list_articles():
        analysis = analyze_article(article)
        save_analysis(analysis)
        score = analysis.risk.risk_score
        scores.append(score)
        articles_out.append(
            {
                "article_id": article.article_id,
                "title": article.title,
                "source": article.source,
                "risk_score": score,
                "factors": analysis.risk.factors,
                "claim_count": len(analysis.claims),
            }
        )
    early = evaluate_early_detection(threshold=50.0)
    avg_risk = sum(scores) / len(scores) if scores else 0.0
    return {
        "article_count": len(articles_out),
        "avg_risk": round(avg_risk, 2),
        "pending_events": pending_local(),
        "model": model_status(),
        "early_detection": {
            "early_detection_rate": early.early_detection_rate,
            "precision": early.precision,
            "recall": early.recall,
            "false_positive_rate": early.false_positive_rate,
            "avg_lead_time_minutes": early.avg_lead_time_minutes,
        },
        "articles": articles_out,
    }
