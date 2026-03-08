from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_api_key: str
    api_key: str = "default-dev-key"
    database_url: str = "sqlite:///./chatbot.db"
    rate_limit: str = "30/minute"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
