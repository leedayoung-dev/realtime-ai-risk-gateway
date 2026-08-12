"""FastAPI AI Security Gateway skeleton."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

from src.config import settings
from src.gateway.service import guard, inspect_text
from src.models import GuardRequest, GuardResponse, InspectionResult, SamplePrompt

app = FastAPI(
    title="AI Security Gateway API",
    version="0.1.0",
    description="AI security detection and policy skeleton (Project D)",
)


def _load_samples() -> list[SamplePrompt]:
    path = Path(settings.sample_data_path)
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [SamplePrompt.model_validate(item) for item in payload["samples"]]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/samples", response_model=list[SamplePrompt])
def samples() -> list[SamplePrompt]:
    return _load_samples()


@app.post("/v1/inspect", response_model=InspectionResult)
def inspect(request: GuardRequest) -> InspectionResult:
    return inspect_text(request.prompt)


@app.post("/v1/guard", response_model=GuardResponse)
def guard_endpoint(request: GuardRequest) -> GuardResponse:
    return guard(request.user_id, request.prompt, request.output)
