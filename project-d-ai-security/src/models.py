from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ThreatCategory(str, Enum):
    NORMAL = "normal"
    DIRECT_INJECTION = "direct_injection"
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    JAILBREAK = "jailbreak"
    PII = "pii"
    CREDENTIAL = "credential"
    INDIRECT_INJECTION = "indirect_injection"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"
    MASK = "mask"


class ToolName(str, Enum):
    SEARCH = "search"
    DB_READ = "db_read"
    DB_WRITE = "db_write"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    EMAIL = "email"
    EXTERNAL_API = "external_api"


class SamplePrompt(BaseModel):
    sample_id: str
    category: ThreatCategory
    text: str


class LayerScore(BaseModel):
    layer: str
    score: float
    labels: list[str] = Field(default_factory=list)


class DlpFinding(BaseModel):
    kind: str
    value: str
    action: PolicyAction


class InspectionResult(BaseModel):
    text: str
    risk_score: float
    layers: list[LayerScore]
    dlp_findings: list[DlpFinding] = Field(default_factory=list)
    action: PolicyAction
    masked_text: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class GuardRequest(BaseModel):
    user_id: str = "anonymous"
    prompt: str
    output: Optional[str] = None


class GuardResponse(BaseModel):
    input_inspection: InspectionResult
    output_inspection: Optional[InspectionResult] = None
    final_action: PolicyAction
    safe_prompt: Optional[str] = None
    safe_output: Optional[str] = None


class AgentToolCall(BaseModel):
    tool: ToolName
    arguments: dict = Field(default_factory=dict)
    call_id: str = "call-001"


class AgentGuardRequest(BaseModel):
    user_id: str = "agent"
    call: AgentToolCall


class AgentGuardResponse(BaseModel):
    call: AgentToolCall
    action: PolicyAction
    allowed: bool
    risk_score: float
    reasons: list[str] = Field(default_factory=list)
    danger_labels: list[str] = Field(default_factory=list)
    dlp_findings: list[DlpFinding] = Field(default_factory=list)
    safe_arguments: Optional[dict] = None
    created_at: datetime = Field(default_factory=utcnow)