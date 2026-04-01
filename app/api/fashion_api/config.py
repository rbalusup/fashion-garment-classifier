"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root .env (two levels up from fashion_api/)
_ROOT_ENV = Path(__file__).parent.parent.parent.parent / ".env"
# Local override inside app/api/ (optional, takes precedence)
_LOCAL_ENV = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str
    fashion_claude_model: str = "claude-3-5-sonnet-20241022"

    # Database
    fashion_database_url: str = "sqlite:///./fashion.db"

    # Storage
    fashion_upload_dir: str = "uploads"
    fashion_max_upload_mb: int = 10

    # Logging
    fashion_log_level: str = "INFO"
    fashion_debug: bool = False

    model_config = {
        "env_file": [str(_ROOT_ENV), str(_LOCAL_ENV)],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def claude_model(self) -> str:
        return self.fashion_claude_model

    @property
    def database_url(self) -> str:
        return self.fashion_database_url

    @property
    def upload_dir(self) -> str:
        return self.fashion_upload_dir

    @property
    def max_upload_bytes(self) -> int:
        return self.fashion_max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
