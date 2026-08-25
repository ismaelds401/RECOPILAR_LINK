from datetime import UTC, datetime, timedelta

from backend.models.event import Event
from backend.services.deduplicator import DuplicateCandidate, is_probable_duplicate


START = datetime(2026, 9, 5, 19, tzinfo=UTC)


def make_event(title: str = "Google Cloud AI Workshop") -> Event:
    return Event(
        title=title,
        slug="event",
        organization="GDG Lima",
        start_date=START,
        timezone="UTC",
        modality="in_person",
        city="Lima",
        country="Peru",
        source_url="https://example.com/event",
        source="GDG",
        source_event_id="1",
        event_hash="a" * 64,
    )


def test_deduplicator_matches_small_title_variation_across_sources() -> None:
    candidate = DuplicateCandidate(
        id="existing",
        title="Workshop: Google Cloud AI",
        start_date=START + timedelta(minutes=10),
        organization="Google Developer Groups Lima",
        city="Lima",
        source="Luma",
    )

    assert is_probable_duplicate(make_event(), candidate)


def test_deduplicator_rejects_different_city_or_time() -> None:
    different_city = DuplicateCandidate(
        id="city",
        title="Google Cloud AI Workshop",
        start_date=START,
        city="Arequipa",
    )
    different_time = DuplicateCandidate(
        id="time",
        title="Google Cloud AI Workshop",
        start_date=START + timedelta(hours=2),
        city="Lima",
    )

    assert not is_probable_duplicate(make_event(), different_city)
    assert not is_probable_duplicate(make_event(), different_time)


def test_deduplicator_rejects_different_title() -> None:
    candidate = DuplicateCandidate(
        id="other",
        title="Python for Data Engineering",
        start_date=START,
        city="Lima",
    )

    assert not is_probable_duplicate(make_event(), candidate)


