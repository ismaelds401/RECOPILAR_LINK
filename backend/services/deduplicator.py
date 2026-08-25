"""Conservative fuzzy duplicate detection across independent providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher

from backend.models.event import Event
from backend.utils.text import normalize_text

MAX_TIME_DIFFERENCE_SECONDS = 30 * 60


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    id: str
    title: str
    start_date: datetime
    organization: str | None = None
    city: str | None = None
    source: str | None = None

    @classmethod
    def from_event(cls, event: Event, identifier: str) -> DuplicateCandidate:
        return cls(
            id=identifier,
            title=event.title,
            start_date=event.start_date,
            organization=event.organization,
            city=event.city,
            source=event.source,
        )

    @classmethod
    def from_database_row(cls, row: dict[str, object]) -> DuplicateCandidate:
        start_date = datetime.fromisoformat(
            str(row["start_date"]).replace("Z", "+00:00")
        )
        return cls(
            id=str(row["id"]),
            title=str(row["title"]),
            start_date=start_date,
            organization=str(row["organization"]) if row.get("organization") else None,
            city=str(row["city"]) if row.get("city") else None,
            source=str(row["source"]) if row.get("source") else None,
        )


def is_probable_duplicate(event: Event, candidate: DuplicateCandidate) -> bool:
    """Match only high-confidence near-identical events to avoid false merges."""
    return candidates_are_probable_duplicates(
        DuplicateCandidate.from_event(event, "incoming"), candidate
    )


def candidates_are_probable_duplicates(
    first: DuplicateCandidate, second: DuplicateCandidate
) -> bool:
    time_difference = abs(
        (
            first.start_date.astimezone(UTC)
            - second.start_date.astimezone(UTC)
        ).total_seconds()
    )
    if time_difference > MAX_TIME_DIFFERENCE_SECONDS:
        return False

    first_city = normalize_text(first.city)
    second_city = normalize_text(second.city)
    if first_city and second_city and first_city != second_city:
        return False

    first_title = normalize_text(first.title)
    second_title = normalize_text(second.title)
    if not first_title or not second_title:
        return False
    if first_title == second_title:
        return True

    similarity = SequenceMatcher(None, first_title, second_title).ratio()
    first_tokens = set(first_title.split())
    second_tokens = set(second_title.split())
    if first_tokens == second_tokens:
        return True
    token_overlap = len(first_tokens & second_tokens) / max(
        1, len(first_tokens | second_tokens)
    )
    if similarity < 0.92 or token_overlap < 0.75:
        return False

    first_org = normalize_text(first.organization)
    second_org = normalize_text(second.organization)
    if not first_org or not second_org:
        return True
    organization_similarity = SequenceMatcher(
        None, first_org, second_org
    ).ratio()
    return organization_similarity >= 0.65 or similarity >= 0.97


def find_duplicate(
    event: Event, candidates: list[DuplicateCandidate]
) -> DuplicateCandidate | None:
    return next(
        (
            candidate
            for candidate in candidates
            if is_probable_duplicate(event, candidate)
        ),
        None,
    )

