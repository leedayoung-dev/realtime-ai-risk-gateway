"""DLP engine for synthetic PII/credential detection (D-F-12, D-F-13)."""

from __future__ import annotations

import re

from src.models import DlpFinding, PolicyAction

_PHONE = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_AWS_KEY = re.compile(r"(?:AWS)?_?SECRET_?ACCESS_?KEY\s*=\s*([A-Za-z0-9/+=]{20,})")
_API_KEY = re.compile(r"(?:api[_-]?key|access[_-]?token)\s*[:=]\s*([A-Za-z0-9\-_]{16,})", re.I)


def scan(text: str) -> list[DlpFinding]:
    findings: list[DlpFinding] = []
    for match in _PHONE.finditer(text):
        findings.append(DlpFinding(kind="phone", value=match.group(0), action=PolicyAction.MASK))
    for match in _EMAIL.finditer(text):
        findings.append(DlpFinding(kind="email", value=match.group(0), action=PolicyAction.MASK))
    for match in _AWS_KEY.finditer(text):
        findings.append(DlpFinding(kind="aws_secret", value=match.group(0), action=PolicyAction.BLOCK))
    for match in _API_KEY.finditer(text):
        findings.append(DlpFinding(kind="api_key", value=match.group(0), action=PolicyAction.BLOCK))
    return findings


def mask_text(text: str, findings: list[DlpFinding]) -> str:
    masked = text
    for finding in findings:
        if finding.action == PolicyAction.MASK:
            masked = masked.replace(finding.value, f"[{finding.kind.upper()}_MASKED]")
    return masked
