"""Models and preference matching for the daily event digest."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backend.utils.text import normalize_text


def _parse_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Expected an ISO date string from Supabase.")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True, slots=True)
class DigestEvent:
    id: str
    title: str
    slug: str
    organization: str | None
    category: str
    tags: tuple[str, ...]
    event_type: str | None
    start_date: datetime
    modality: str
    city: str | None
    is_free: bool | None
    registration_url: str | None
    source_url: str
    source: str
    first_seen_at: datetime

    @property
    def destination_url(self) -> str:
        return self.registration_url or self.source_url

    @classmethod
    def from_database_row(cls, row: dict[str, object]) -> DigestEvent:
        tags = row.get("tags")
        return cls(
            id=str(row["id"]),
            title=str(row["title"]),
            slug=str(row["slug"]),
            organization=str(row["organization"]) if row.get("organization") else None,
            category=str(row["category"]),
            tags=tuple(str(tag) for tag in tags) if isinstance(tags, list) else (),
            event_type=str(row["event_type"]) if row.get("event_type") else None,
            start_date=_parse_datetime(row["start_date"]),
            modality=str(row["modality"]),
            city=str(row["city"]) if row.get("city") else None,
            is_free=row.get("is_free") if isinstance(row.get("is_free"), bool) else None,
            registration_url=(
                str(row["registration_url"]) if row.get("registration_url") else None
            ),
            source_url=str(row["source_url"]),
            source=str(row["source"]),
            first_seen_at=_parse_datetime(row["first_seen_at"]),
        )


@dataclass(frozen=True, slots=True)
class DigestPreferences:
    categories: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    cities: frozenset[str] = field(default_factory=frozenset)
    modalities: frozenset[str] = field(default_factory=frozenset)
    organizations: frozenset[str] = field(default_factory=frozenset)
    keywords: frozenset[str] = field(default_factory=frozenset)
    free_only: bool = False

    def matches(self, event: DigestEvent) -> bool:
        if self.categories and event.category not in self.categories:
            return False
        if self.tags and not self.tags.intersection(event.tags):
            return False
        if self.cities and (event.city or "") not in self.cities:
            return False
        if self.modalities and event.modality not in self.modalities:
            return False
        if self.organizations and (event.organization or "") not in self.organizations:
            return False
        if self.free_only and event.is_free is not True:
            return False
        if self.keywords:
            haystack = normalize_text(
                " ".join(
                    (
                        event.title,
                        event.organization or "",
                        event.category,
                        event.event_type or "",
                        " ".join(event.tags),
                    )
                )
            )
            if not any(normalize_text(keyword) in haystack for keyword in self.keywords):
                return False
        return True

