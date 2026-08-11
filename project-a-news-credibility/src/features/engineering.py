"""Feature engineering skeleton (A-F-07, A-F-08)."""

from __future__ import annotations

from src.models import Article, Claim, Evidence


def build_features(
    article: Article,
    claims: list[Claim],
    evidence: list[Evidence],
) -> dict[str, float | int | str]:
    """Build a minimal feature dict for risk scoring.

    M3 will expand source/propagation features and persist to Feast + Redis.
    """
    supporting = sum(1 for e in evidence if e.evidence_type.value == "supporting")
    contradicting = sum(1 for e in evidence if e.evidence_type.value == "contradicting")
    official = sum(1 for e in evidence if e.evidence_type.value == "official")

    return {
        "article_id": article.article_id,
        "source": article.source,
        "claim_count": len(claims),
        "evidence_supporting": supporting,
        "evidence_contradicting": contradicting,
        "evidence_official": official,
        "content_length": len(article.content),
        # Propagation placeholders (A-F-08)
        "share_velocity": 0.0,
        "share_acceleration": 0.0,
        "burst": 0.0,
        "engagement_pattern": 0.0,
    }
