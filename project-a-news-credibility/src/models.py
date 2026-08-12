from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceType(str, Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    OFFICIAL = "official"


class Article(BaseModel):
    article_id: str
    title: str
    source: str
    url: str
    published_at: datetime
    content: str
    share_count: int = 0
    share_delta_1m: int = 0
    share_delta_5m: int = 0


class Claim(BaseModel):
    claim_id: str
    article_id: str
    text: str
    claim_type: str = "factual"
    confidence: float = Field(default=0.5, ge=0, le=1)
    extracted_at: datetime = Field(default_factory=utcnow)


class Evidence(BaseModel):
    evidence_id: str
    claim_id: str
    evidence_type: EvidenceType
    source: str
    snippet: str
    relevance: float = Field(default=0.0, ge=0, le=1)
    collected_at: datetime = Field(default_factory=utcnow)
    url: Optional[str] = None


class CredibilityRisk(BaseModel):
    article_id: str
    risk_score: float = Field(ge=0, le=100)
    updated_at: datetime = Field(default_factory=utcnow)
    factors: dict[str, str] = Field(default_factory=dict)
    claim_count: int = 0
    evidence_count: int = 0


class ArticleAnalysis(BaseModel):
    article_id: str
    title: str
    claims: list[Claim]
    evidence: list[Evidence]
    risk: CredibilityRisk


class RiskHistoryPoint(BaseModel):
    article_id: str
    risk_score: float
    updated_at: datetime
    factors: dict[str, str] = Field(default_factory=dict)
