"""News collector — samples / RSS publish helpers (A-F-01)."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.config import settings
from src.models import Article
from src.streaming.bus import publish_many

logger = logging.getLogger(__name__)


def load_sample_articles(path: str | None = None) -> list[Article]:
    data_path = Path(path or settings.sample_data_path)
    with data_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [Article.model_validate(item) for item in payload["articles"]]


def publish_articles(articles: list[Article], dry_run: bool = False) -> dict:
    if dry_run:
        for article in articles:
            logger.info("[dry-run] -> %s", article.article_id)
        return {"published": len(articles), "backends": {"dry-run": len(articles)}}
    from src.store.registry import upsert_many

    upsert_many(articles)
    return publish_many(articles)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    articles = load_sample_articles()
    result = publish_articles(articles)
    logger.info("Published: %s", result)


if __name__ == "__main__":
    main()
