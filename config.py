"""LearnFast — centralised application settings.

All configuration is loaded from environment variables and the .env file.
Import the shared ``settings`` singleton anywhere you need a config value:

    from config import settings
    key = settings.groq_api_key
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings for LearnFast.

    Values are read from environment variables (case-insensitive) and from
    a ``.env`` file in the project root, with environment variables taking
    priority.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Required — the app will not start without this.
    # ------------------------------------------------------------------
    groq_api_key: str = Field(..., description="Groq API key for the LLM.")

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------
    secret_key: str = Field(
        default="dev-secret-change-me",
        description=(
            "Flask session secret key. "
            "Generate a strong value with: python -c \"import secrets; print(secrets.token_hex(32))\""
        ),
    )

    # ------------------------------------------------------------------
    # Email (optional — verification codes print to console if not set)
    # ------------------------------------------------------------------
    sender_email: str = Field(default="", description="Gmail address used to send verification codes.")
    sender_password: str = Field(default="", description="Gmail app password for the sender account.")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    db_path: Path = Field(
        default=Path(__file__).parent / "learnfast.db",
        description="Filesystem path to the SQLite database file.",
    )

    # ------------------------------------------------------------------
    # Groq / LLM
    # ------------------------------------------------------------------
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model identifier.",
    )

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    host: str = Field(default="0.0.0.0", description="Bind address for the dev server.")
    port: int = Field(default=5001, description="Port for the dev server.")
    debug: bool = Field(default=False, description="Enable Flask debug mode.")


# Single shared instance — import this rather than constructing a new Settings().
settings = Settings()
