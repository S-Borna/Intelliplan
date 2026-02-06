"""Application configuration."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Intelliplan"
    app_env: str = "development"
    database_url: str = "sqlite:///./intelliplan.db"
    openai_api_key: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
