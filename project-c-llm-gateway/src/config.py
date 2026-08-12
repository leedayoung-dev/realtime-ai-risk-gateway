from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gateway_default_timeout_ms: int = 1500
    gateway_force_fallback: bool = False


settings = Settings()
