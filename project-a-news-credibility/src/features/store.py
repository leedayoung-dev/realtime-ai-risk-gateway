"""Feature store — Redis with in-memory fallback (A-F-09)."""

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


def _get_redis():
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
        logger.info("Connected to Redis feature store at %s", settings.redis_url)
        return _redis_client
    except Exception as exc:  # noqa: BLE001
        _redis_failed = True
        logger.warning("Redis unavailable (%s). Using in-memory feature store.", exc)
        return None


def _key(article_id: str) -> str:
    return f"features:article:{article_id}"


def put_features(article_id: str, features: dict[str, Any], ttl: int | None = None) -> str:
    ttl = ttl if ttl is not None else settings.feature_ttl_seconds
    payload = {k: v for k, v in features.items()}
    payload["_stored_at"] = time.time()
    backend = "memory"

    client = _get_redis()
    if client is not None:
        client.setex(_key(article_id), ttl, json.dumps(payload, default=str))
        backend = "redis"
    else:
        _MEMORY[article_id] = (time.time() + ttl, payload)
    return backend


def get_features(article_id: str) -> dict[str, Any] | None:
    client = _get_redis()
    if client is not None:
        raw = client.get(_key(article_id))
        if not raw:
            return None
        return json.loads(raw)

    item = _MEMORY.get(article_id)
    if item is None:
        return None
    expires_at, payload = item
    if time.time() > expires_at:
        _MEMORY.pop(article_id, None)
        return None
    return payload


def list_feature_keys() -> list[str]:
    client = _get_redis()
    if client is not None:
        return [k.replace("features:article:", "") for k in client.keys("features:article:*")]
    now = time.time()
    alive = []
    for article_id, (expires_at, _) in list(_MEMORY.items()):
        if now <= expires_at:
            alive.append(article_id)
        else:
            _MEMORY.pop(article_id, None)
    return alive
