"""Configuration management for the GitHub Event Listener service."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # GitHub App Configuration (Required)
    github_app_id: str
    github_installation_id: str
    github_app_private_key: str

    # Service Configuration
    event_listener_host: str = "0.0.0.0"
    event_listener_port: int = 8000
    log_level: str = "INFO"

    # Orchestrator Configuration
    orchestrator_timeout: int = 300
    max_concurrent_events: int = 10

    # Optional GitHub Enterprise Configuration
    github_api_url: str = "https://api.github.com"

    # Security
    allowed_github_ips: Optional[str] = None

    @field_validator("github_app_private_key")
    @classmethod
    def validate_private_key(cls, v):
        """Ensure private key is properly formatted."""
        if not v.startswith("-----BEGIN"):
            # Try to load from file if it's a path
            if os.path.exists(v):
                with open(v) as f:
                    return f.read()
            raise ValueError("Private key must be PEM formatted or a valid file path")
        return v

    @field_validator("allowed_github_ips")
    @classmethod
    def parse_allowed_ips(cls, v):
        """Parse comma-separated IP list."""
        if v:
            return [ip.strip() for ip in v.split(",")]
        return None

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @property
    def github_headers(self) -> dict:
        """Common headers for GitHub API requests."""
        return {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Configured settings object
    """
    return Settings()


# Convenience function for accessing settings
settings = get_settings()
