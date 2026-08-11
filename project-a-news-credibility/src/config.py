from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_news_topic: str = "news.raw"
    redis_url: str = "redis://localhost:6379/0"
    sample_data_path: str = "data/samples/articles.json"


settings = Settings()
