import os
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ABACADABA"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    POSTGRES_SERVER: str = os.environ.get("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "exam_bot")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @property
    def get_db_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # Backend
    ]

    # OpenAI
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # Google Cloud Vision
    GOOGLE_APPLICATION_CREDENTIALS: str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Stripe
    STRIPE_API_KEY: str = os.environ.get("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
