"""Defense layer comparison experiments."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.config import settings
from src.detection.engine import llm_judge_score, ml_score, rule_score
from src.dlp.scanner import scan
from src.models import PolicyAction, SamplePrompt, ThreatCategory
from src.policy.engine import decide


class LayerCaseResult(BaseModel):
    sample_id: str
    category: ThreatCategory
    is_attack: bool
    action: PolicyAction
    risk_score: float
    blocked_or_masked: bool
    true_positive: bool
    false_positive: bool
    false_negative: bool
    true_negative: bool


class LayerReport(BaseModel):
    layer: str
    attack_success_rate: float = Field(description="Attack not blocked/masked")
    detection_rate: float
    false_positive_rate: float
    n_cases: int
    cases: list[LayerCaseResult] = Field(default_factory=list)


class DefenseExperimentReport(BaseModel):
    layers: list[LayerReport]
    best_layer: str


_ATTACK = {
    ThreatCategory.DIRECT_INJECTION,
    ThreatCategory.SYSTEM_PROMPT_EXTRACTION,
    ThreatCategory.JAILBREAK,
    ThreatCategory.INDIRECT_INJECTION,
    ThreatCategory.CREDENTIAL,
}


def _load_samples() -> list[SamplePrompt]:
    path = Path(settings.sample_data_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [SamplePrompt.model_validate(item) for item in payload["samples"]]


def _is_attack(category: ThreatCategory) -> bool:
    return category in _ATTACK or category == ThreatCategory.PII


def _decide_for_layer(layer: str, text: str) -> tuple[PolicyAction, float, list[str]]:
    findings = scan(text)
    if layer == "baseline":
        return PolicyAction.ALLOW, 0.0, ["no_security_gateway"]

    if layer == "rule":
        layers = [rule_score(text)]
    elif layer == "ml":
        layers = [ml_score(text)]
    elif layer == "llm_judge":
        layers = [llm_judge_score(text)]
    elif layer == "rule_ml":
        layers = [rule_score(text), ml_score(text)]
    else:  # full
        layers = [rule_score(text), ml_score(text), llm_judge_score(text)]

    # For single-layer experiments use that layer score as risk;
    # for multi-layer use max (aligned with production peak logic).
    risk = max(l.score for l in layers)
    action, reasons = decide(risk, findings)
    return action, risk, reasons


def _metrics(cases: list[LayerCaseResult]) -> tuple[float, float, float]:
    attacks = [c for c in cases if c.is_attack]
    normals = [c for c in cases if not c.is_attack]
    if attacks:
        missed = sum(1 for c in attacks if not c.blocked_or_masked)
        asr = missed / len(attacks)
        detection = sum(1 for c in attacks if c.blocked_or_masked) / len(attacks)
    else:
        asr, detection = 0.0, 0.0
    fpr = (
        sum(1 for c in normals if c.blocked_or_masked) / len(normals) if normals else 0.0
    )
    return round(asr, 3), round(detection, 3), round(fpr, 3)


def evaluate_layer(layer: str) -> LayerReport:
    cases: list[LayerCaseResult] = []
    for sample in _load_samples():
        attack = _is_attack(sample.category)
        # PII expected to MASK (counts as mitigated), credential/injection to BLOCK/REVIEW+
        action, risk, _ = _decide_for_layer(layer, sample.text)
        mitigated = action in {PolicyAction.BLOCK, PolicyAction.MASK, PolicyAction.REVIEW}
        # For PII, REVIEW alone without mask is weak; treat MASK/BLOCK as success, REVIEW ok-ish
        if sample.category == ThreatCategory.PII:
            mitigated = action in {PolicyAction.MASK, PolicyAction.BLOCK, PolicyAction.REVIEW}
        if sample.category == ThreatCategory.NORMAL:
            mitigated = action in {PolicyAction.BLOCK}  # only hard block is FP for normal

        tp = attack and mitigated
        fp = (not attack) and mitigated
        fn = attack and not mitigated
        tn = (not attack) and not mitigated
        cases.append(
            LayerCaseResult(
                sample_id=sample.sample_id,
                category=sample.category,
                is_attack=attack,
                action=action,
                risk_score=risk,
                blocked_or_masked=mitigated,
                true_positive=tp,
                false_positive=fp,
                false_negative=fn,
                true_negative=tn,
            )
        )

    asr, detection, fpr = _metrics(cases)
    return LayerReport(
        layer=layer,
        attack_success_rate=asr,
        detection_rate=detection,
        false_positive_rate=fpr,
        n_cases=len(cases),
        cases=cases,
    )


def run_defense_experiments() -> DefenseExperimentReport:
    layers = ["baseline", "rule", "ml", "llm_judge", "rule_ml", "full"]
    preference = {name: i for i, name in enumerate(layers)}
    reports = [evaluate_layer(name) for name in layers]
    # Best = lowest ASR, then lowest FPR, then prefer fuller stacks
    best = sorted(
        reports,
        key=lambda r: (r.attack_success_rate, r.false_positive_rate, -preference[r.layer]),
    )[0]
    return DefenseExperimentReport(layers=reports, best_layer=best.layer)
