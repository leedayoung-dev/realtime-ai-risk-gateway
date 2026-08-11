"""Streaming pipeline skeleton (A-F-02).

M1 uses a lightweight consumer loop. PySpark Structured Streaming
can replace this module in a later milestone without changing domain contracts.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from src.config import settings
from src.models import Article

logger = logging.getLogger(__name__)

ArticleHandler = Callable[[Article], None]


def process_article(article: Article, handler: ArticleHandler | None = None) -> dict[str, Any]:
    """Single-article processing hook used by streaming and local tests."""
    if handler:
        handler(article)
    return {
        "article_id": article.article_id,
        "status": "accepted",
        "source": article.source,
    }


def run_consumer(handler: ArticleHandler | None = None, max_messages: int | None = None) -> int:
    """Consume raw news events from Kafka and invoke the processing hook."""
    try:
        from kafka import KafkaConsumer
    except ImportError as exc:
        raise RuntimeError("kafka-python is required") from exc

    consumer = KafkaConsumer(
        settings.kafka_news_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    processed = 0
    try:
        for message in consumer:
            article = Article.model_validate(message.value)
            result = process_article(article, handler=handler)
            logger.info("Processed %s", result)
            processed += 1
            if max_messages is not None and processed >= max_messages:
                break
    finally:
        consumer.close()
    return processed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_consumer(max_messages=10)
