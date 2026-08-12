"""HTTP client for Project D AI Security Gateway."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.config import settings
from src.models import SecurityInfo


def security_status() -> dict[str, Any]:
    url = settings.security_gateway_url.rstrip("/")
    enabled = settings.security_enabled
    if not enabled:
        return {"enabled": False, "available": False, "url": url, "detail": "disabled"}
    try:
        with httpx.Client(timeout=settings.security_timeout_ms / 1000) as client:
            resp = client.get(f"{url}/health")
            resp.raise_for_status()
            return {"enabled": True, "available": True, "url": url, "detail": resp.json()}
    except Exception as exc:  # noqa: BLE001 — demo fail-open path
        return {"enabled": True, "available": False, "url": url, "detail": str(exc)}


def guard_prompt(
    prompt: str,
    *,
    user_id: str = "gateway",
    output: Optional[str] = None,
) -> SecurityInfo:
    """Call D /v1/guard. On failure, fail-open with available=False."""
    url = settings.security_gateway_url.rstrip("/")
    if not settings.security_enabled:
        return SecurityInfo(enabled=False, available=False, gateway_url=url)

    try:
        payload: dict[str, Any] = {"user_id": user_id, "prompt": prompt}
        if output is not None:
            payload["output"] = output
        with httpx.Client(timeout=settings.security_timeout_ms / 1000) as client:
            resp = client.post(f"{url}/v1/guard", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return SecurityInfo(
            enabled=True,
            available=False,
            gateway_url=url,
            reasons=[f"security_gateway_unavailable: {exc}"],
        )

    input_insp = data.get("input_inspection") or {}
    return SecurityInfo(
        enabled=True,
        available=True,
        final_action=data.get("final_action"),
        risk_score=input_insp.get("risk_score"),
        reasons=list(input_insp.get("reasons") or []),
        safe_prompt=data.get("safe_prompt"),
        safe_output=data.get("safe_output"),
        masked=(data.get("final_action") == "mask"),
        gateway_url=url,
    )
