"""Feature store with Redis + memory fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)
_MEMORY: dict[str, tuple[float, dict[str, Any]]] = {}
_redis_client = None
_redis_failed = False


def _redis():
    global _redis_client, _redis_failed
    if _redis_failed:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _redis_client = client
        return client
    except Exception as exc:  # noqa: BLE001
        _redis_failed = True
        logger.warning("Redis unavailable (%s). Using memory feature store.", exc)
        return None


def put_features(user_id: str, features: dict[str, Any]) -> str:
    payload = dict(features)
    payload["_stored_at"] = time.time()
    client = _redis()
    key = f"fraud:features:{user_id}"
    if client is not None:
        client.setex(key, settings.feature_ttl_seconds, json.dumps(payload, default=str))
        return "redis"
    _MEMORY[user_id] = (time.time() + settings.feature_ttl_seconds, payload)
    return "memory"


def get_features(user_id: str) -> dict[str, Any] | None:
    client = _redis()
    if client is not None:
        raw = client.get(f"fraud:features:{user_id}")
        return json.loads(raw) if raw else None
    item = _MEMORY.get(user_id)
    if not item:
        return None
    expires, payload = item
    if time.time() > expires:
        _MEMORY.pop(user_id, None)
        return None
    return payload
