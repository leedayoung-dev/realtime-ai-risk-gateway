"""Local event bus — Kafka when available, in-memory queue otherwise."""

from __future__ import annotations

import json
import logging
import queue
from typing import Any

from src.config import settings
from src.models import Article

logger = logging.getLogger(__name__)

_LOCAL_QUEUE: queue.Queue[Article] = queue.Queue()


def publish(article: Article) -> str:
    """Publish one article. Returns backend name: kafka|memory."""
    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            request_timeout_ms=2000,
            api_version_auto_timeout_ms=2000,
        )
        try:
            future = producer.send(settings.kafka_news_topic, article.model_dump(mode="json"))
            future.get(timeout=2)
            producer.flush()
        finally:
            producer.close()
        return "kafka"
    except Exception as exc:  # noqa: BLE001
        logger.debug("Kafka publish failed (%s). Using memory bus.", exc)
        _LOCAL_QUEUE.put(article)
        return "memory"


def publish_many(articles: list[Article]) -> dict[str, Any]:
    backends: dict[str, int] = {}
    for article in articles:
        backend = publish(article)
        backends[backend] = backends.get(backend, 0) + 1
    return {"published": len(articles), "backends": backends}


def consume_local(max_messages: int | None = None) -> list[Article]:
    items: list[Article] = []
    while max_messages is None or len(items) < max_messages:
        try:
            items.append(_LOCAL_QUEUE.get_nowait())
        except queue.Empty:
            break
    return items


def pending_local() -> int:
    return _LOCAL_QUEUE.qsize()
