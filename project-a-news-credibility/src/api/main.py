"""FastAPI skeleton for credibility risk serving (A-F-12)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.claims.extractor import extract_claims
from src.collector.news_collector import load_sample_articles
from src.evidence.retriever import retrieve_evidence
from src.features.engineering import build_features
from src.models import Claim, CredibilityRisk
from src.risk.scorer import score_risk

app = FastAPI(
    title="News Credibility API",
    version="0.1.0",
    description="Real-time news credibility risk skeleton (Project A)",
)

_ARTICLE_INDEX = {a.article_id: a for a in load_sample_articles()}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/articles/{article_id}/claims", response_model=list[Claim])
def get_claims(article_id: str) -> list[Claim]:
    article = _ARTICLE_INDEX.get(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return extract_claims(article)


@app.get("/v1/articles/{article_id}/risk", response_model=CredibilityRisk)
def get_risk(article_id: str) -> CredibilityRisk:
    article = _ARTICLE_INDEX.get(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")

    claims = extract_claims(article)
    evidence = [ev for claim in claims for ev in retrieve_evidence(claim)]
    features = build_features(article, claims, evidence)
    return score_risk(features)
