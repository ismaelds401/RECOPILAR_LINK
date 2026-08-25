"""Deterministic text normalization and identifiers."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import UTC, datetime


def normalize_text(value: str | None) -> str:
    """Normalize case, accents, punctuation and repeated whitespace."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    words_only = re.sub(r"[^a-z0-9]+", " ", without_accents)
    return " ".join(words_only.split())


def build_event_hash(
    title: str,
    start_date: datetime,
    organization: str | None,
    city: str | None,
) -> str:
    """Create the cross-source SHA-256 deduplication key."""
    utc_start = start_date.astimezone(UTC).replace(second=0, microsecond=0)
    parts = (
        normalize_text(title),
        utc_start.isoformat(),
        normalize_text(organization),
        normalize_text(city),
    )
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def build_slug(title: str, start_date: datetime, source_event_id: str) -> str:
    """Build a readable, stable slug without requiring it to be globally unique."""
    title_part = normalize_text(title).replace(" ", "-")[:72].strip("-") or "event"
    source_part = normalize_text(source_event_id).replace(" ", "-")[-12:]
    return f"{title_part}-{start_date:%Y-%m-%d}-{source_part}".strip("-")


def infer_event_type(title: str, tags: list[str] | None = None) -> str | None:
    """Infer only the broad event format; topical classification is Phase 5."""
    normalized = normalize_text(" ".join([title, *(tags or [])]))
    rules = (
        (("hackathon", "hackaton"), "hackathon"),
        (("workshop", "taller", "hands on"), "workshop"),
        (("webinar",), "webinar"),
        (("meetup", "meet up"), "meetup"),
        (("conference", "conferencia", "summit", "devfest"), "conference"),
        (("bootcamp",), "bootcamp"),
        (("talk", "charla"), "talk"),
    )
    for keywords, event_type in rules:
        if any(keyword in normalized for keyword in keywords):
            return event_type
    return None

