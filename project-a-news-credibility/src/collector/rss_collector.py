"""RSS / fixture news collector."""

from __future__ import annotations

import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from src.config import settings
from src.models import Article
from src.streaming.bus import publish_many
from src.store.registry import upsert_many

logger = logging.getLogger(__name__)

_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", text or "")).strip()


def _article_id_from_url(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"rss-{digest}"


def _parse_rss_xml(xml_text: str, source_fallback: str = "rss") -> list[Article]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall(".//item")
    articles: list[Article] = []

    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or ""
        pub = item.findtext("pubDate")
        if not title or not link:
            continue
        try:
            published_at = parsedate_to_datetime(pub) if pub else datetime.now(timezone.utc)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
        except Exception:  # noqa: BLE001
            published_at = datetime.now(timezone.utc)

        host = urlparse(link).netloc or source_fallback
        content = _strip_html(description) or title
        articles.append(
            Article(
                article_id=_article_id_from_url(link),
                title=title,
                source=host,
                url=link,
                published_at=published_at,
                content=content,
                share_count=0,
                share_delta_1m=0,
                share_delta_5m=0,
            )
        )
    return articles


def load_fixture_articles(path: str | None = None) -> list[Article]:
    fixture = Path(path or settings.rss_fixture_path)
    xml_text = fixture.read_text(encoding="utf-8")
    return _parse_rss_xml(xml_text, source_fallback="fixture-rss")


def fetch_rss_articles(feed_url: str | None = None, timeout: float = 8.0) -> list[Article]:
    url = feed_url or settings.rss_feeds.split(",")[0].strip()
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url, headers={"User-Agent": "realtime-ai-risk-gateway/0.4"})
        response.raise_for_status()
        return _parse_rss_xml(response.text, source_fallback=urlparse(url).netloc or "rss")


def collect_news(
    *,
    use_fixture: bool | None = None,
    feed_url: str | None = None,
    max_items: int | None = None,
    publish: bool = True,
) -> dict:
    prefer_fixture = settings.collect_prefer_fixture if use_fixture is None else use_fixture
    source = "fixture"
    try:
        if prefer_fixture:
            articles = load_fixture_articles()
        else:
            articles = fetch_rss_articles(feed_url=feed_url)
            source = "rss"
    except Exception as exc:  # noqa: BLE001
        logger.warning("RSS fetch failed (%s). Falling back to fixture.", exc)
        articles = load_fixture_articles()
        source = "fixture_fallback"

    limit = max_items or settings.rss_max_items
    articles = articles[:limit]
    upsert_many(articles)
    bus_result = publish_many(articles) if publish else {"published": 0, "backends": {}}
    return {
        "source": source,
        "collected": len(articles),
        "article_ids": [a.article_id for a in articles],
        "bus": bus_result,
    }
