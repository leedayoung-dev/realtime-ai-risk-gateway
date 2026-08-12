"""Request analyzer — classify prompt intent (C-F-02)."""

from __future__ import annotations

from src.models import RequestType

_COMPLEX_HINTS = ("비교", "설계", "단계", "근거", "분석", "why", "compare", "architecture")
_LONG_HINTS = ("문서", "요약", "long", "context", "transcript", "전문")


def analyze_request(prompt: str) -> RequestType:
    text = prompt.strip()
    lower = text.lower()

    if len(text) >= 800 or any(h in lower for h in _LONG_HINTS):
        return RequestType.LONG_CONTEXT
    if any(h in lower for h in _COMPLEX_HINTS) or len(text) >= 160:
        return RequestType.COMPLEX_REASONING
    return RequestType.SIMPLE
