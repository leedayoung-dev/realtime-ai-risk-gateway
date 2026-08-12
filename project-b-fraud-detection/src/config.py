from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9093"
    kafka_events_topic: str = "fraud.events"
    redis_url: str = "redis://localhost:6380/0"
    sample_data_path: str = "data/samples/users.json"
    training_data_path: str = "data/samples/training_labels.json"
    supervised_model_path: str = "artifacts/supervised_model.joblib"
    anomaly_model_path: str = "artifacts/anomaly_model.joblib"
    feature_ttl_seconds: int = 3600
    use_ml_model: bool = True


settings = Settings()
