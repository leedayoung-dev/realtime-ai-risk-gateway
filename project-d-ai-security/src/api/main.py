"""FastAPI AI Security Gateway."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.agent.guard import evaluate_tool_call
from src.agent.policy import tool_policy_table
from src.config import settings
from src.evaluation.defense import DefenseExperimentReport, run_defense_experiments
from src.gateway.service import guard, inspect_text
from src.models import (
    AgentGuardRequest,
    AgentGuardResponse,
    AgentToolCall,
    GuardRequest,
    GuardResponse,
    InspectionResult,
    SamplePrompt,
)
from src.monitoring.store import aggregate, clear_events, list_events, user_profile

STATIC_DIR = Path(__file__).resolve().parent / "static"
AGENT_SAMPLES = Path("data/samples/agent_calls.json")

app = FastAPI(
    title="AI Security Gateway API",
    version="0.4.0",
    description="AI security detection, policy, agent tool guard, monitoring (Project D)",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _load_samples() -> list[SamplePrompt]:
    path = Path(settings.sample_data_path)
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [SamplePrompt.model_validate(item) for item in payload["samples"]]


def _load_agent_samples() -> list[AgentToolCall]:
    payload = json.loads(AGENT_SAMPLES.read_text(encoding="utf-8"))
    return [AgentToolCall.model_validate(item) for item in payload["calls"]]


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.4.0"}


@app.get("/v1/samples", response_model=list[SamplePrompt])
def samples() -> list[SamplePrompt]:
    return _load_samples()


@app.post("/v1/inspect", response_model=InspectionResult)
def inspect(request: GuardRequest) -> InspectionResult:
    return inspect_text(request.prompt)


@app.post("/v1/guard", response_model=GuardResponse)
def guard_endpoint(request: GuardRequest) -> GuardResponse:
    return guard(request.user_id, request.prompt, request.output)


@app.get("/v1/agent/policy")
def agent_policy() -> dict:
    return {"tools": tool_policy_table()}


@app.get("/v1/agent/samples", response_model=list[AgentToolCall])
def agent_samples() -> list[AgentToolCall]:
    return _load_agent_samples()


@app.post("/v1/agent/guard", response_model=AgentGuardResponse)
def agent_guard(request: AgentGuardRequest) -> AgentGuardResponse:
    return evaluate_tool_call(request.call, user_id=request.user_id, persist=True)


@app.post("/v1/agent/demo/seed")
def agent_seed() -> dict:
    results = []
    for call in _load_agent_samples():
        results.append(
            evaluate_tool_call(call, user_id="agent-demo", persist=True).model_dump(mode="json")
        )
    return {"seeded": len(results), "results": results, "metrics": aggregate()}


@app.get("/v1/events")
def events(limit: int = 50) -> list[dict]:
    return [e.model_dump(mode="json") for e in list_events(limit=limit)]


@app.get("/v1/metrics")
def metrics() -> dict:
    return aggregate()


@app.get("/v1/users/{user_id}/risk")
def user_risk(user_id: str) -> dict:
    return user_profile(user_id)


@app.post("/v1/demo/seed")
def seed_demo() -> dict:
    """Seed prompt traffic from samples under a few demo users."""
    clear_events()
    users = ["alice", "bob", "carol"]
    seeded = 0
    for i, sample in enumerate(_load_samples()):
        uid = users[i % len(users)]
        guard(uid, sample.text, persist=True)
        seeded += 1
    return {"seeded": seeded, "metrics": aggregate()}


@app.get("/v1/experiments/defense", response_model=DefenseExperimentReport)
def defense_experiments() -> DefenseExperimentReport:
    return run_defense_experiments()


@app.get("/v1/dashboard/overview")
def dashboard_overview() -> dict:
    return {
        "live": aggregate(),
        "recent": [e.model_dump(mode="json") for e in list_events(limit=20)],
        "thresholds": {
            "block": settings.security_block_threshold,
            "review": settings.security_review_threshold,
        },
        "layers": ["rule", "ml", "llm_judge", "dlp", "policy", "agent"],
        "agent_policy": tool_policy_table(),
    }
