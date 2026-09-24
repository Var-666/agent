from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal[
    "development",
    "test",
    "production",
]

LogLevel = Literal[
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FLOW_AGENT_",
        extra="ignore",
        frozen=True,
    )

    environment: Environment = "development"
    workspace_root: Path = Path("workspace")
    log_level: LogLevel = "INFO"
    
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None


def load_settings() -> Settings:
    return Settings()
