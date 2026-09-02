from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(ROOT_ENV, ".env"), extra="ignore")

    database_url: str = "postgresql://domovoy:domovoy@localhost:5433/domovoy"
    test_database_url: str = "postgresql://domovoy:domovoy@localhost:5433/domovoy_test"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    app_env: str = "dev"
    demo_now: str = ""
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
