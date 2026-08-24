"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when a required setting is missing or unsafe."""


@dataclass(frozen=True, slots=True)
class Settings:
    supabase_url: str
    supabase_secret_key: str


def get_settings() -> Settings:
    """Load backend-only credentials from the repository's local .env file."""
    load_dotenv()

    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY)")
    if missing:
        raise ConfigurationError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    if not url.startswith("https://") or not url.endswith(".supabase.co"):
        raise ConfigurationError(
            "SUPABASE_URL must look like https://<project-ref>.supabase.co"
        )

    return Settings(supabase_url=url, supabase_secret_key=key)
