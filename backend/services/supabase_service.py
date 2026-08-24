"""Create the server-side Supabase client in one place."""

from __future__ import annotations

from supabase import Client, ClientOptions, create_client

from backend.config import get_settings


def create_backend_client() -> Client:
    """Return a Supabase client with backend-only credentials and timeouts."""
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_secret_key,
        options=ClientOptions(
            postgrest_client_timeout=15,
            storage_client_timeout=15,
            schema="public",
        ),
    )
