"""Environment configuration for daily Gmail digests."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

from backend.config import ConfigurationError
from backend.notifications.models import DigestPreferences


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
VALID_MODALITIES = {"in_person", "virtual", "hybrid"}


def _csv(name: str) -> frozenset[str]:
    return frozenset(
        value.strip() for value in os.getenv(name, "").split(",") if value.strip()
    )


def _positive_int(name: str, default: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if not 1 <= value <= maximum:
        raise ConfigurationError(f"{name} must be between 1 and {maximum}.")
    return value


def _boolean(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    if raw in {"true", "1", "yes", "si", "sí"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    raise ConfigurationError(f"{name} must be true or false.")


@dataclass(frozen=True, slots=True)
class DigestSettings:
    sender_email: str
    app_password: str
    recipients: tuple[str, ...]
    site_url: str
    lookback_hours: int
    max_events: int
    preferences: DigestPreferences


def get_digest_settings(*, require_gmail: bool = True) -> DigestSettings:
    load_dotenv()
    sender = os.getenv("GMAIL_SENDER_EMAIL", "").strip().lower()
    password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    recipient_values = os.getenv("DIGEST_RECIPIENT_EMAILS", "").strip()
    recipients = tuple(
        dict.fromkeys(
            email.strip().lower()
            for email in recipient_values.split(",")
            if email.strip()
        )
    )

    if require_gmail:
        missing = []
        if not sender:
            missing.append("GMAIL_SENDER_EMAIL")
        if not password:
            missing.append("GMAIL_APP_PASSWORD")
        if not recipients:
            missing.append("DIGEST_RECIPIENT_EMAILS")
        if missing:
            raise ConfigurationError(
                "Missing required digest environment variables: " + ", ".join(missing)
            )

    for email in ((sender,) if sender else ()) + recipients:
        if not EMAIL_PATTERN.fullmatch(email):
            raise ConfigurationError(f"Invalid email address in digest settings: {email}")
    if password and len(password) != 16:
        raise ConfigurationError("GMAIL_APP_PASSWORD must contain 16 characters.")

    modalities = _csv("DIGEST_MODALITIES")
    invalid_modalities = modalities - VALID_MODALITIES
    if invalid_modalities:
        raise ConfigurationError(
            "DIGEST_MODALITIES contains invalid values: "
            + ", ".join(sorted(invalid_modalities))
        )

    site_url = os.getenv(
        "DIGEST_SITE_URL", "https://recopilar-link.pages.dev"
    ).strip().rstrip("/")
    if not site_url.startswith("https://"):
        raise ConfigurationError("DIGEST_SITE_URL must use https://")

    preferences = DigestPreferences(
        categories=_csv("DIGEST_CATEGORIES"),
        tags=_csv("DIGEST_TAGS"),
        cities=_csv("DIGEST_CITIES"),
        modalities=modalities,
        organizations=_csv("DIGEST_ORGANIZATIONS"),
        keywords=_csv("DIGEST_KEYWORDS"),
        free_only=_boolean("DIGEST_FREE_ONLY"),
    )
    return DigestSettings(
        sender_email=sender,
        app_password=password,
        recipients=recipients,
        site_url=site_url,
        lookback_hours=_positive_int("DIGEST_LOOKBACK_HOURS", 48, 168),
        max_events=_positive_int("DIGEST_MAX_EVENTS", 20, 100),
        preferences=preferences,
    )

