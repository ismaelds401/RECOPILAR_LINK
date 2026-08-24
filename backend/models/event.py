"""Universal normalized event model used by every connector."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Event:
    title: str
    slug: str
    start_date: datetime
    timezone: str
    modality: str
    source_url: str
    source: str
    source_event_id: str
    event_hash: str
    description: str | None = None
    organization: str | None = None
    category: str = "Other"
    subcategory: str | None = None
    tags: list[str] = field(default_factory=list)
    event_type: str | None = None
    end_date: datetime | None = None
    venue: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_free: bool | None = None
    price: float | None = None
    currency: str | None = None
    registration_url: str | None = None
    image_url: str | None = None
    status: str = "published"

    def to_database_payload(self) -> dict[str, object]:
        """Return only columns accepted by the Phase 1 events table."""
        payload = asdict(self)
        payload["start_date"] = self.start_date.isoformat()
        if self.end_date is not None:
            payload["end_date"] = self.end_date.isoformat()
        return payload


