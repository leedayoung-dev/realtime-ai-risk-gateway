"""Streaming pipeline — consume articles and run credibility analysis."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from src.config import settings
from src.models import Article, ArticleAnalysis
from src.pipeline.analyze import analyze_article
from src.store.registry import save_analysis, upsert_article
from src.streaming.bus import consume_local

logger = logging.getLogger(__name__)

ArticleHandler = Callable[[Article], ArticleAnalysis | None]


def process_article(article: Article, handler: ArticleHandler | None = None) -> dict[str, Any]:
    upsert_article(article)
    if handler:
        analysis = handler(article)
    else:
        analysis = analyze_article(article)
        save_analysis(analysis)

    return {
        "article_id": article.article_id,
        "status": "analyzed",
        "source": article.source,
        "risk_score": None if analysis is None else analysis.risk.risk_score,
    }


def run_local_batch(max_messages: int | None = None) -> dict[str, Any]:
    articles = consume_local(max_messages=max_messages)
    results = [process_article(article) for article in articles]
    return {"processed": len(results), "results": results}


def run_consumer(handler: ArticleHandler | None = None, max_messages: int | None = None) -> int:
    """Consume raw news events from Kafka and invoke analysis."""
    try:
        from kafka import KafkaConsumer
    except ImportError as exc:
        raise RuntimeError("kafka-python is required") from exc

    consumer = KafkaConsumer(
        settings.kafka_news_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        consumer_timeout_ms=3000,
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
    # Prefer local batch if Kafka is down
    local = run_local_batch()
    if local["processed"]:
        logger.info("Local batch: %s", local)
    else:
        run_consumer(max_messages=10)
