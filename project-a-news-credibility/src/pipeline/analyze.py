"""End-to-end analysis pipeline for an article."""

from __future__ import annotations

from src.claims.extractor import extract_claims
from src.evidence.retriever import retrieve_evidence
from src.features.engineering import build_features
from src.features.store import put_features
from src.models import Article, ArticleAnalysis
from src.risk.scorer import score_risk


def analyze_article(article: Article, persist_features: bool = True) -> ArticleAnalysis:
    claims = extract_claims(article)
    evidence = [ev for claim in claims for ev in retrieve_evidence(claim)]
    features = build_features(article, claims, evidence)
    if persist_features:
        backend = put_features(article.article_id, features)
        features["feature_store"] = backend
    risk = score_risk(features)
    return ArticleAnalysis(
        article_id=article.article_id,
        title=article.title,
        claims=claims,
        evidence=evidence,
        risk=risk,
    )
