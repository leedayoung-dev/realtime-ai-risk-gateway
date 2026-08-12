from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    LOGIN = "login"
    LISTING = "listing"
    CHAT = "chat"
    TRANSACTION = "transaction"
    REPORT = "report"


class ListingSnapshot(BaseModel):
    listing_id: str
    price: float
    category_avg_price: float
    title: str


class BehaviorSnapshot(BaseModel):
    messages_per_5m: int = 0
    listing_burst: int = 0
    new_users_contacted: int = 0
    external_contact_attempt: int = 0


class NetworkSnapshot(BaseModel):
    connected_users: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    user_id: str
    account_age_days: int
    transaction_count: int
    report_count: int
    listings: list[ListingSnapshot] = Field(default_factory=list)
    behavior: BehaviorSnapshot = Field(default_factory=BehaviorSnapshot)
    network: NetworkSnapshot = Field(default_factory=NetworkSnapshot)
    label_hint: Optional[str] = None


class UserEvent(BaseModel):
    event_id: str
    event_type: EventType
    user_id: str
    occurred_at: datetime = Field(default_factory=utcnow)
    payload: dict = Field(default_factory=dict)


class FraudRisk(BaseModel):
    user_id: str
    risk_score: float = Field(ge=0, le=100)
    model: str
    updated_at: datetime = Field(default_factory=utcnow)
    factors: dict[str, str] = Field(default_factory=dict)


class ModelComparison(BaseModel):
    user_id: str
    supervised: FraudRisk
    anomaly: FraudRisk
    agreement: bool
    delta: float
