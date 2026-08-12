"""FastAPI LLM Gateway — routing, agent, A/B insights + D security."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.agent.runner import run_agent
from src.agent.store import list_agent_runs
from src.config import settings
from src.evaluation.runner import (
    analytics_summary,
    evaluate_prompt,
    run_benchmark,
)
from src.evaluation.store import aggregate, list_history, seed_demo_traffic
from src.insights.pull import pull_all
from src.insights.service import RiskInsight, RiskInsightRequest, generate_insight
from src.insights.store import list_insights, record_insight
from src.models import AgentRunRequest, AgentRunResponse, ChatRequest, ChatResponse, EvaluationResult
from src.routing.engine import route_chat, routing_policy
from src.security.client import security_status

app = FastAPI(
    title="LLM Gateway API",
    version="0.6.0",
    description="LLM routing, A/B risk insights, agent tools + Project D gates (Project C)",
)

_DASHBOARD = Path(__file__).resolve().parent / "static" / "dashboard.html"


@app.get("/")
def root() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD)


@app.get("/health")
def health() -> dict:
    live = aggregate()
    return {
        "status": "ok",
        "version": "0.6.0",
        "request_count": live["request_count"],
        "security": security_status(),
        "insights": len(list_insights(limit=100)),
    }


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return route_chat(
        request.prompt,
        user_id=request.user_id,
        force_fallback=request.force_fallback,
        simulate_primary_failure=request.simulate_primary_failure,
        enable_security=request.enable_security,
    )


@app.post("/v1/agent/run", response_model=AgentRunResponse)
def agent_run(request: AgentRunRequest) -> AgentRunResponse:
    return run_agent(request)


@app.get("/v1/agent/history")
def agent_history(limit: int = 20) -> list[dict]:
    return [r.model_dump(mode="json") for r in list_agent_runs(limit=limit)]


@app.post("/v1/insights", response_model=RiskInsight)
def create_insight(request: RiskInsightRequest) -> RiskInsight:
    """Push endpoint for Project A/B high-risk events."""
    return record_insight(generate_insight(request))


@app.get("/v1/insights")
def insights(limit: int = 20) -> list[dict]:
    return [i.model_dump(mode="json") for i in list_insights(limit=limit)]


@app.post("/v1/insights/pull")
def insights_pull(threshold: float | None = None) -> dict:
    """Pull high-risk rows from A/B dashboards and generate summaries."""
    return pull_all(threshold=threshold)


@app.post("/v1/evaluate", response_model=EvaluationResult)
def evaluate(request: ChatRequest) -> EvaluationResult:
    return evaluate_prompt(request.prompt)


@app.get("/v1/analytics/summary")
def summary() -> dict:
    return analytics_summary()


@app.get("/v1/analytics/history")
def history(limit: int = 50) -> list[ChatResponse]:
    return list_history(limit=limit)


@app.get("/v1/evaluation/benchmark")
def benchmark() -> dict:
    return run_benchmark().model_dump(mode="json")


@app.post("/v1/demo/seed")
def demo_seed() -> dict:
    n = seed_demo_traffic()
    return {"seeded": n, "live": aggregate()}


@app.get("/v1/security/status")
def sec_status() -> dict:
    return security_status()


@app.get("/v1/dashboard/overview")
def overview() -> dict:
    live = aggregate()
    recent = [
        {
            "request_type": item.request_type.value,
            "primary_model": item.primary_model.value,
            "used_model": item.used_model.value,
            "fallback_used": item.fallback_used,
            "latency_ms": item.latency_ms,
            "cost_usd": item.cost_usd,
            "blocked": item.blocked,
            "security_action": item.security.final_action if item.security else None,
            "content": item.content[:120],
        }
        for item in list_history(limit=20)
    ]
    agent_recent = [
        {
            "prompt": r.prompt[:80],
            "tools_planned": r.tools_planned,
            "tools_executed": r.tools_executed,
            "tools_blocked": r.tools_blocked,
            "tools_review": r.tools_review,
            "traces": [
                {
                    "tool": t.tool,
                    "status": t.status,
                    "action": t.guard.action if t.guard else None,
                }
                for t in r.traces
            ],
            "blocked_chat": r.chat.blocked,
        }
        for r in list_agent_runs(limit=10)
    ]
    insight_recent = [
        {
            "source": i.source,
            "entity_id": i.entity_id,
            "risk_score": i.risk_score,
            "label": i.label,
            "summary": i.summary[:140],
            "blocked": i.chat.blocked,
            "model": i.chat.used_model.value,
        }
        for i in list_insights(limit=10)
    ]
    return {
        "routing_policy": routing_policy(),
        "live": live,
        "by_model": live.get("by_model", {}),
        "recent": recent,
        "agent_recent": agent_recent,
        "insight_recent": insight_recent,
        "catalog": analytics_summary()["models"],
        "security": security_status(),
        "security_config": {
            "enabled": settings.security_enabled,
            "url": settings.security_gateway_url,
        },
        "insight_config": {
            "threshold": settings.insight_risk_threshold,
            "news_api_url": settings.news_api_url,
            "fraud_api_url": settings.fraud_api_url,
        },
    }
