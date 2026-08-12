"""Claim extraction (A-F-03, A-F-04) — M2 verifiable-claim heuristics."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from src.models import Article, Claim

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?다요음])\s+|(?<=\.)\s+")
_FACTUAL_CUES = re.compile(
    r"(발표|확인|검토|주장|보고|밝혔다|전했다|따르면|동결|인상|허가|임상|효과|공식)"
)
_WEAK_CUES = re.compile(r"(생각|느낌|것 같다|분위기|전망된다)$")


def _stable_claim_id(article_id: str, text: str) -> str:
    digest = hashlib.sha1(f"{article_id}:{text}".encode("utf-8")).hexdigest()[:10]
    return f"clm-{digest}"


def _score_sentence(text: str) -> tuple[float, str]:
    score = 0.35
    claim_type = "general"
    if _FACTUAL_CUES.search(text):
        score += 0.35
        claim_type = "factual"
    if re.search(r"\d", text):
        score += 0.15
        claim_type = "quantitative"
    if any(x in text for x in ("공식", "보도자료", "발표")):
        score += 0.15
        claim_type = "official_claim"
    if _WEAK_CUES.search(text):
        score -= 0.25
    return max(0.0, min(1.0, score)), claim_type


def extract_claims(article: Article, min_confidence: float = 0.45) -> list[Claim]:
    """Extract verifiable claim candidates with stable IDs and confidence."""
    raw_sentences = [s.strip() for s in _SENTENCE_SPLIT.split(article.content) if s.strip()]
    if article.title.strip():
        raw_sentences.insert(0, article.title.strip())

    now = datetime.now(timezone.utc)
    claims: list[Claim] = []
    seen: set[str] = set()

    for sentence in raw_sentences:
        if len(sentence) < 10:
            continue
        confidence, claim_type = _score_sentence(sentence)
        if confidence < min_confidence:
            continue
        claim_id = _stable_claim_id(article.article_id, sentence)
        if claim_id in seen:
            continue
        seen.add(claim_id)
        claims.append(
            Claim(
                claim_id=claim_id,
                article_id=article.article_id,
                text=sentence,
                claim_type=claim_type,
                confidence=round(confidence, 2),
                extracted_at=now,
            )
        )

    if not claims:
        claims.append(
            Claim(
                claim_id=_stable_claim_id(article.article_id, article.title),
                article_id=article.article_id,
                text=article.title,
                claim_type="title",
                confidence=0.4,
                extracted_at=now,
            )
        )
    return claims
