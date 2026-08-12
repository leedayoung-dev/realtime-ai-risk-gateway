"""In-memory article registry shared by collector, streaming, and API."""

from __future__ import annotations

from threading import RLock

from src.models import Article, ArticleAnalysis

_lock = RLock()
_articles: dict[str, Article] = {}
_analyses: dict[str, ArticleAnalysis] = {}
_initialized = False


def _ensure_seeded() -> None:
    global _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        from src.collector.news_collector import load_sample_articles

        for article in load_sample_articles():
            _articles[article.article_id] = article
        _initialized = True


def upsert_article(article: Article) -> Article:
    _ensure_seeded()
    with _lock:
        _articles[article.article_id] = article
        return article


def upsert_many(articles: list[Article]) -> int:
    for article in articles:
        upsert_article(article)
    return len(articles)


def get_article(article_id: str) -> Article | None:
    _ensure_seeded()
    with _lock:
        return _articles.get(article_id)


def list_articles() -> list[Article]:
    _ensure_seeded()
    with _lock:
        return list(_articles.values())


def save_analysis(analysis: ArticleAnalysis) -> ArticleAnalysis:
    with _lock:
        _analyses[analysis.article_id] = analysis
        return analysis


def get_analysis(article_id: str) -> ArticleAnalysis | None:
    with _lock:
        return _analyses.get(article_id)


def list_analyses() -> list[ArticleAnalysis]:
    with _lock:
        return list(_analyses.values())
