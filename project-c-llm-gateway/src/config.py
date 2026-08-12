from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gateway_default_timeout_ms: int = 1500
    gateway_force_fallback: bool = False

    # Project D AI Security Gateway (fail-open if unreachable)
    security_enabled: bool = True
    security_gateway_url: str = "http://127.0.0.1:8003"
    security_timeout_ms: int = 800

    # Project A/B risk → insight generation
    news_api_url: str = "http://127.0.0.1:8000"
    fraud_api_url: str = "http://127.0.0.1:8001"
    insight_risk_threshold: float = 50.0
    insight_timeout_ms: int = 3000


settings = Settings()
