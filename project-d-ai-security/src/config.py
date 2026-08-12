from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    security_block_threshold: float = 80
    security_review_threshold: float = 50
    sample_data_path: str = "data/samples/prompts.json"


settings = Settings()
