"""Feature engineering (A-F-07, A-F-08) — M2 source/propagation + evidence quality."""

from __future__ import annotations

from src.models import Article, Claim, Evidence

_SOURCE_TRUST = {
    "official-wire": 0.9,
    "example-news": 0.55,
    "market-wire": 0.45,
}


def build_features(
    article: Article,
    claims: list[Claim],
    evidence: list[Evidence],
) -> dict[str, float | int | str]:
    matched = [e for e in evidence if e.source != "gap" and e.relevance > 0]
    supporting = [e for e in matched if e.evidence_type.value == "supporting"]
    contradicting = [e for e in matched if e.evidence_type.value == "contradicting"]
    official = [e for e in matched if e.evidence_type.value == "official"]

    avg_claim_conf = (
        sum(c.confidence for c in claims) / len(claims) if claims else 0.0
    )
    avg_evidence_rel = (
        sum(e.relevance for e in matched) / len(matched) if matched else 0.0
    )

    # Propagation proxies from sample metadata
    share_velocity = float(article.share_delta_1m)
    share_acceleration = float(article.share_delta_5m - article.share_delta_1m * 5)
    burst = 1.0 if article.share_delta_1m >= 50 else 0.0

    return {
        "article_id": article.article_id,
        "source": article.source,
        "source_trust": _SOURCE_TRUST.get(article.source, 0.5),
        "claim_count": len(claims),
        "avg_claim_confidence": round(avg_claim_conf, 3),
        "evidence_supporting": len(supporting),
        "evidence_contradicting": len(contradicting),
        "evidence_official": len(official),
        "evidence_matched": len(matched),
        "avg_evidence_relevance": round(avg_evidence_rel, 3),
        "content_length": len(article.content),
        "share_velocity": share_velocity,
        "share_acceleration": share_acceleration,
        "burst": burst,
        "engagement_pattern": float(article.share_count),
    }
