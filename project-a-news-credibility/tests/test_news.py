"""Project A claim / risk smoke tests."""

from __future__ import annotations

from datetime import datetime, timezone

from src.claims.extractor import extract_claims
from src.models import Article
from src.pipeline.analyze import analyze_article


def _sample_article() -> Article:
    return Article(
        article_id="test-001",
        title="정부가 금리 인상을 공식 발표했다",
        content="정부가 오늘 금리를 0.25%p 인상했다고 공식 발표했다. 시장은 추가 인상을 전망한다.",
        source="test-source",
        published_at=datetime.now(timezone.utc),
        url="https://example.com/a",
    )


def test_extract_claims() -> None:
    claims = extract_claims(_sample_article(), min_confidence=0.3)
    assert len(claims) >= 1
    assert claims[0].text


def test_analyze_article_returns_risk() -> None:
    analysis = analyze_article(_sample_article(), persist_features=False)
    assert 0 <= analysis.risk.risk_score <= 100
    assert analysis.article_id == "test-001"
