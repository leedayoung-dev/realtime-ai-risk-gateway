"""FastAPI LLM Gateway skeleton (C-F-01)."""

from __future__ import annotations

from fastapi import FastAPI

from src.evaluation.runner import analytics_summary, evaluate_prompt
from src.models import ChatRequest, ChatResponse, EvaluationResult
from src.routing.engine import route_chat

app = FastAPI(
    title="LLM Gateway API",
    version="0.1.0",
    description="LLM routing and evaluation skeleton (Project C)",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return route_chat(
        request.prompt,
        force_fallback=request.force_fallback,
        simulate_primary_failure=request.simulate_primary_failure,
    )


@app.post("/v1/evaluate", response_model=EvaluationResult)
def evaluate(request: ChatRequest) -> EvaluationResult:
    return evaluate_prompt(request.prompt)


@app.get("/v1/analytics/summary")
def summary() -> dict:
    return analytics_summary()
