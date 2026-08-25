"""Framework-independent filters shared by validation and the future UI logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from backend.models.event import Event
from backend.utils.text import normalize_text


@dataclass(frozen=True, slots=True)
class EventFilters:
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    categories: set[str] = field(default_factory=set)
    organizations: set[str] = field(default_factory=set)
    modalities: set[str] = field(default_factory=set)
    cities: set[str] = field(default_factory=set)
    is_free: bool | None = None
    event_types: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    upcoming_only: bool = True


def filter_events(
    events: list[Event],
    filters: EventFilters,
    *,
    now: datetime | None = None,
) -> list[Event]:
    """Apply combinable filters and return events ordered by start date."""
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return sorted(
        (event for event in events if _matches(event, filters, current)),
        key=lambda event: event.start_date,
    )


def _matches(event: Event, filters: EventFilters, now: datetime) -> bool:
    if event.status != "published":
        return False
    start_utc = event.start_date.astimezone(UTC)
    if filters.upcoming_only and (event.end_date or event.start_date).astimezone(UTC) < now:
        return False
    if filters.date_from and start_utc < filters.date_from.astimezone(UTC):
        return False
    if filters.date_to and start_utc > filters.date_to.astimezone(UTC):
        return False
    if filters.categories and event.category not in filters.categories:
        return False
    if filters.organizations and (event.organization or "") not in filters.organizations:
        return False
    if filters.modalities and event.modality not in filters.modalities:
        return False
    if filters.cities and (event.city or "") not in filters.cities:
        return False
    if filters.is_free is not None and event.is_free is not filters.is_free:
        return False
    if filters.event_types and (event.event_type or "") not in filters.event_types:
        return False
    if filters.tags and not filters.tags.issubset(set(event.tags)):
        return False
    if filters.search:
        haystack = normalize_text(
            " ".join(
                (
                    event.title,
                    event.description or "",
                    event.organization or "",
                    event.category,
                    " ".join(event.tags),
                )
            )
        )
        if normalize_text(filters.search) not in haystack:
            return False
    return True

