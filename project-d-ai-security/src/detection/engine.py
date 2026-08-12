"""Multi-layer detection stubs (D-F-08 ~ D-F-11)."""

from __future__ import annotations

import re

from src.models import LayerScore

_INJECTION_PATTERNS = [
    r"이전 지시(?:를|을)?\s*무시",
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"시스템 설정(?:을|를)?\s*출력",
    r"internal\s+instruction",
    r"jailbreak",
    r"개발자 모드",
]

_EXTRACTION_PATTERNS = [
    r"시스템\s*프롬프트",
    r"내부 지시",
    r"system\s*prompt",
    r"hidden\s*prompt",
]


def _match_score(text: str, patterns: list[str], hit_score: float) -> tuple[float, list[str]]:
    labels: list[str] = []
    score = 0.0
    lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE) or re.search(pattern, lower):
            labels.append(pattern)
            score = max(score, hit_score)
    return score, labels


def rule_score(text: str) -> LayerScore:
    inj, inj_labels = _match_score(text, _INJECTION_PATTERNS, 90.0)
    ext, ext_labels = _match_score(text, _EXTRACTION_PATTERNS, 85.0)
    score = max(inj, ext)
    return LayerScore(layer="rule", score=score, labels=inj_labels + ext_labels)


def ml_score(text: str) -> LayerScore:
    """Lightweight lexical proxy for ML classifier."""
    tokens = [
        "무시",
        "override",
        "bypass",
        "탈취",
        "유출",
        "비밀번호",
        "api key",
        "api_key",
        "jailbreak",
        "hidden prompt",
        "시스템 설정",
        "내부 지시",
    ]
    lower = text.lower()
    hits = [t for t in tokens if t.lower() in lower]
    score = min(95.0, 22.0 * len(hits))
    return LayerScore(layer="ml", score=score, labels=hits)


def llm_judge_score(text: str) -> LayerScore:
    """Deterministic judge stub based on explicit attack cues."""
    cues = ["시스템 설정", "내부 지시", "ignore previous", "jailbreak"]
    hits = [c for c in cues if c.lower() in text.lower()]
    score = 88.0 if hits else 5.0
    return LayerScore(layer="llm_judge", score=score, labels=hits)


def combined_risk(layers: list[LayerScore]) -> float:
    if not layers:
        return 0.0
    # Weighted blend, but keep strong single-layer hits visible for policy decisions
    weights = {"rule": 0.5, "ml": 0.3, "llm_judge": 0.2}
    total_w = 0.0
    acc = 0.0
    peak = 0.0
    for layer in layers:
        w = weights.get(layer.layer, 0.2)
        acc += layer.score * w
        total_w += w
        peak = max(peak, layer.score)
    blended = acc / total_w
    return round(max(blended, peak), 1)
