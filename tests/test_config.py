"""Offline tests for environment validation; no Supabase project is contacted."""

import pytest

from backend.config import ConfigurationError, get_settings


def test_missing_configuration_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setattr("backend.config.load_dotenv", lambda: False)

    with pytest.raises(ConfigurationError):
        get_settings()


def test_valid_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co/")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_test")
    monkeypatch.setattr("backend.config.load_dotenv", lambda: False)

    settings = get_settings()

    assert settings.supabase_url == "https://example.supabase.co"
    assert settings.supabase_secret_key == "sb_secret_test"
