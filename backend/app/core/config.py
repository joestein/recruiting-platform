from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Recruiting Platform API"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ALGORITHM: str = "HS256"

    # DB
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./dev.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | List[str] = ["http://localhost:8501"]

    # OpenAI / matching / agent
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    MATCHING_USE_OPENAI: bool = False  # set true in env to enable embeddings

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
