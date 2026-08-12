"""LLM provider stubs — no external API calls in M1."""

from __future__ import annotations

import time
from dataclasses import dataclass

from src.models import ModelName


@dataclass(frozen=True)
class ProviderResult:
    model: ModelName
    content: str
    latency_ms: int
    cost_usd: float
    quality: float


_CATALOG: dict[ModelName, dict[str, float | str]] = {
    ModelName.GPT: {"latency_ms": 1200, "cost_usd": 0.012, "quality": 91, "label": "GPT"},
    ModelName.CLAUDE: {"latency_ms": 1500, "cost_usd": 0.015, "quality": 94, "label": "Claude"},
    ModelName.GEMINI: {"latency_ms": 800, "cost_usd": 0.007, "quality": 89, "label": "Gemini"},
}


def invoke_model(model: ModelName, prompt: str, fail: bool = False) -> ProviderResult:
    if fail:
        raise TimeoutError(f"{model.value} primary timeout")

    meta = _CATALOG[model]
    # Tiny sleep to simulate work without slowing tests much
    time.sleep(0.01)
    content = f"[{meta['label']} stub] {prompt[:120]}"
    return ProviderResult(
        model=model,
        content=content,
        latency_ms=int(meta["latency_ms"]),
        cost_usd=float(meta["cost_usd"]),
        quality=float(meta["quality"]),
    )


def list_catalog() -> dict[ModelName, dict[str, float | str]]:
    return _CATALOG
