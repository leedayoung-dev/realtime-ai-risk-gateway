"""Multi-model evaluation (C-F-06, C-F-07)."""

from __future__ import annotations

from src.models import EvaluationResult, ModelMetrics, ModelName
from src.providers.stub import invoke_model, list_catalog


def evaluate_prompt(prompt: str) -> EvaluationResult:
    results: list[ModelMetrics] = []
    for model in ModelName:
        out = invoke_model(model, prompt)
        results.append(
            ModelMetrics(
                model=model,
                quality=out.quality,
                latency_ms=out.latency_ms,
                cost_usd=out.cost_usd,
                available=True,
            )
        )

    # Prefer higher quality, then lower cost, then lower latency
    recommended = sorted(
        results,
        key=lambda m: (-m.quality, m.cost_usd, m.latency_ms),
    )[0].model
    return EvaluationResult(prompt=prompt, results=results, recommended_model=recommended)


def analytics_summary() -> dict:
    catalog = list_catalog()
    return {
        "models": [
            {
                "model": model.value,
                "quality": meta["quality"],
                "latency_ms": meta["latency_ms"],
                "cost_usd": meta["cost_usd"],
            }
            for model, meta in catalog.items()
        ],
        "routing_policy": {
            "simple": "gemini → gpt",
            "complex_reasoning": "claude → gpt",
            "long_context": "gpt → claude",
        },
    }
