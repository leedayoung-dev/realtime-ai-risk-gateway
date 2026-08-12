"""Evidence retrieval against local corpus (A-F-05, A-F-06)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from src.models import Claim, Evidence, EvidenceType

_TOKEN = re.compile(r"[A-Za-z0-9]+|[가-힣]{2,}")


@lru_cache(maxsize=1)
def _load_corpus(path: str = "data/samples/evidence_corpus.json") -> list[dict]:
    data_path = Path(path)
    with data_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return list(payload["corpus"])


def _tokenize(text: str) -> set[str]:
    return {p.lower() for p in _TOKEN.findall(text) if len(p) >= 2}


def _relevance(claim_text: str, keywords: list[str], snippet: str) -> float:
    claim_tokens = _tokenize(claim_text)
    key_tokens = {k.lower() for k in keywords}
    snip_tokens = _tokenize(snippet)
    if not claim_tokens:
        return 0.0
    key_hits = len(claim_tokens & key_tokens)
    snip_hits = len(claim_tokens & snip_tokens)
    if key_hits == 0 and snip_hits == 0:
        return 0.0
    score = min(1.0, key_hits * 0.28 + snip_hits * 0.12)
    return round(score, 3)


def retrieve_evidence(claim: Claim, min_relevance: float = 0.2, top_k: int = 3) -> list[Evidence]:
    """Rank corpus documents for a claim and return typed evidence."""
    now = datetime.now(timezone.utc)
    ranked: list[tuple[float, dict]] = []
    for doc in _load_corpus():
        rel = _relevance(claim.text, doc.get("keywords", []), doc["snippet"])
        if rel >= min_relevance:
            ranked.append((rel, doc))

    ranked.sort(key=lambda x: x[0], reverse=True)
    evidence: list[Evidence] = []
    for rel, doc in ranked[:top_k]:
        evidence.append(
            Evidence(
                evidence_id=f"{doc['doc_id']}-{claim.claim_id[-6:]}",
                claim_id=claim.claim_id,
                evidence_type=EvidenceType(doc["evidence_type"]),
                source=doc["source"],
                snippet=doc["snippet"],
                relevance=rel,
                collected_at=now,
                url=doc.get("url"),
            )
        )

    present = {e.evidence_type for e in evidence}
    for etype in EvidenceType:
        if etype not in present:
            evidence.append(
                Evidence(
                    evidence_id=f"gap-{etype.value}-{claim.claim_id[-6:]}",
                    claim_id=claim.claim_id,
                    evidence_type=etype,
                    source="gap",
                    snippet=f"No {etype.value} evidence matched above threshold",
                    relevance=0.0,
                    collected_at=now,
                )
            )
    return evidence
