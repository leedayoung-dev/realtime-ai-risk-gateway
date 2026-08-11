"""News collector — load articles and publish to Kafka (A-F-01)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config import settings
from src.models import Article

logger = logging.getLogger(__name__)


def load_sample_articles(path: str | None = None) -> list[Article]:
    data_path = Path(path or settings.sample_data_path)
    with data_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [Article.model_validate(item) for item in payload["articles"]]


def publish_articles(articles: list[Article], dry_run: bool = False) -> int:
    """Publish articles to Kafka. Falls back to dry-run logging if broker is unavailable."""
    topic = settings.kafka_news_topic
    if dry_run:
        for article in articles:
            logger.info("[dry-run] %s -> %s", topic, article.article_id)
        return len(articles)

    try:
        from kafka import KafkaProducer
    except ImportError as exc:
        raise RuntimeError("kafka-python is required") from exc

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )
    try:
        for article in articles:
            producer.send(topic, article.model_dump(mode="json"))
        producer.flush()
    finally:
        producer.close()
    return len(articles)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    articles = load_sample_articles()
    try:
        count = publish_articles(articles, dry_run=False)
        logger.info("Published %s articles to %s", count, settings.kafka_news_topic)
    except Exception as exc:  # noqa: BLE001 — M1 stub: allow local run without Kafka
        logger.warning("Kafka publish failed (%s). Running dry-run.", exc)
        publish_articles(articles, dry_run=True)


if __name__ == "__main__":
    main()
