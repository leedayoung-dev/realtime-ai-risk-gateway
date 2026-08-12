from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_news_topic: str = "news.raw"
    redis_url: str = "redis://localhost:6379/0"
    sample_data_path: str = "data/samples/articles.json"
    evidence_corpus_path: str = "data/samples/evidence_corpus.json"
    training_data_path: str = "data/samples/training_labels.json"
    model_path: str = "artifacts/risk_model.joblib"
    feature_ttl_seconds: int = 3600
    use_ml_model: bool = True
    rss_feeds: str = "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best"
    rss_fixture_path: str = "data/samples/rss_fixture.xml"
    rss_max_items: int = 8
    collect_prefer_fixture: bool = False

    # Project C risk insights (fail-open)
    insight_push_enabled: bool = True
    llm_gateway_url: str = "http://127.0.0.1:8002"
    insight_push_threshold: float = 50.0
    insight_push_timeout_ms: int = 2000


settings = Settings()
