"""Evidence retrieval skeleton (A-F-05, A-F-06)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.models import Claim, Evidence, EvidenceType


def retrieve_evidence(claim: Claim) -> list[Evidence]:
    """Return placeholder evidence slots for a claim.

    M2 will connect external search / official sources.
    """
    now = datetime.now(timezone.utc)
    return [
        Evidence(
            evidence_id=f"ev-{uuid4().hex[:10]}",
            claim_id=claim.claim_id,
            evidence_type=EvidenceType.SUPPORTING,
            source="stub-supporting",
            snippet=f"[stub] Potential support for: {claim.text[:80]}",
            collected_at=now,
        ),
        Evidence(
            evidence_id=f"ev-{uuid4().hex[:10]}",
            claim_id=claim.claim_id,
            evidence_type=EvidenceType.CONTRADICTING,
            source="stub-contradicting",
            snippet=f"[stub] Potential contradiction for: {claim.text[:80]}",
            collected_at=now,
        ),
        Evidence(
            evidence_id=f"ev-{uuid4().hex[:10]}",
            claim_id=claim.claim_id,
            evidence_type=EvidenceType.OFFICIAL,
            source="stub-official",
            snippet="[stub] Official source not yet retrieved",
            collected_at=now,
        ),
    ]
