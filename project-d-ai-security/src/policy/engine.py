"""Policy engine — ALLOW / REVIEW / BLOCK / MASK (D-F-03)."""

from __future__ import annotations

from src.config import settings
from src.models import DlpFinding, PolicyAction


def decide(risk_score: float, findings: list[DlpFinding]) -> tuple[PolicyAction, list[str]]:
    reasons: list[str] = []

    if any(f.action == PolicyAction.BLOCK for f in findings):
        reasons.append("credential_or_secret_detected")
        return PolicyAction.BLOCK, reasons

    if risk_score >= settings.security_block_threshold:
        reasons.append(f"prompt_injection_risk>={settings.security_block_threshold}")
        return PolicyAction.BLOCK, reasons

    if any(f.action == PolicyAction.MASK for f in findings):
        reasons.append("pii_detected")
        return PolicyAction.MASK, reasons

    if risk_score >= settings.security_review_threshold:
        reasons.append(f"risk_in_review_band>={settings.security_review_threshold}")
        return PolicyAction.REVIEW, reasons

    reasons.append("risk_below_threshold")
    return PolicyAction.ALLOW, reasons
