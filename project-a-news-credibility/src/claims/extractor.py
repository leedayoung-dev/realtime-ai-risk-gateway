"""Claim extraction skeleton (A-F-03, A-F-04)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from src.models import Article, Claim

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?다요음음])\s+|(?<=\.)\s+")


def extract_claims(article: Article) -> list[Claim]:
    """Split article content into verifiable claim candidates.

    M2 will replace heuristic splitting with an NLP-based extractor.
    """
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(article.content) if s.strip()]
    now = datetime.now(timezone.utc)
    claims: list[Claim] = []
    for sentence in sentences:
        if len(sentence) < 12:
            continue
        claims.append(
            Claim(
                claim_id=f"clm-{uuid4().hex[:10]}",
                article_id=article.article_id,
                text=sentence,
                extracted_at=now,
            )
        )
    if not claims:
        claims.append(
            Claim(
                claim_id=f"clm-{uuid4().hex[:10]}",
                article_id=article.article_id,
                text=article.title,
                extracted_at=now,
            )
        )
    return claims
