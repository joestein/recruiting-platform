from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Graph backends
    GRAPH_BACKEND: str = "age"  # "age" or "neptune"
    AGE_HOST: str = "localhost"
    AGE_PORT: int = 5432
    AGE_DB: str = "recruiting"
    AGE_USER: str = "age"
    AGE_PASSWORD: str = "agepassword"
    AGE_GRAPH_NAME: str = "recruiting_graph"

    NEPTUNE_ENDPOINT: Optional[str] = None
    NEPTUNE_PORT: Optional[int] = None
    NEPTUNE_REGION: Optional[str] = None
    NEPTUNE_USE_HTTPS: bool = True
    NEPTUNE_USE_BOLT: bool = False

    # Seeding
    SEED_JOBS_FILE: str = "backend/app/data/seed_jobs.yaml"
    SEED_DEMO_PASSWORD: str = "changeme123"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
