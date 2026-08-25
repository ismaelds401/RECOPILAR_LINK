from datetime import UTC, datetime, timedelta

from backend.models.event import Event
from backend.services.event_filter import EventFilters, filter_events


NOW = datetime(2026, 9, 1, tzinfo=UTC)


def make_event(
    title: str,
    *,
    days: int,
    category: str,
    modality: str,
    city: str | None,
    is_free: bool | None,
    tags: list[str],
) -> Event:
    return Event(
        title=title,
        slug=title.lower().replace(" ", "-"),
        organization="Tech Community",
        category=category,
        tags=tags,
        event_type="workshop",
        start_date=NOW + timedelta(days=days),
        timezone="UTC",
        modality=modality,
        city=city,
        country="Peru" if city else None,
        is_free=is_free,
        source_url="https://example.com/event",
        source="Test",
        source_event_id=title,
        event_hash=("a" if title.startswith("AI") else "b") * 64,
    )


def test_filters_combine_search_category_modality_city_and_free() -> None:
    events = [
        make_event(
            "AI Workshop Lima",
            days=2,
            category="Artificial Intelligence",
            modality="in_person",
            city="Lima",
            is_free=True,
            tags=["AI", "Python"],
        ),
        make_event(
            "Cloud Webinar",
            days=1,
            category="Cloud",
            modality="virtual",
            city=None,
            is_free=True,
            tags=["AWS"],
        ),
    ]
    filters = EventFilters(
        search="python",
        categories={"Artificial Intelligence"},
        modalities={"in_person"},
        cities={"Lima"},
        is_free=True,
        event_types={"workshop"},
        tags={"AI"},
    )

    result = filter_events(events, filters, now=NOW)

    assert [event.title for event in result] == ["AI Workshop Lima"]


def test_filters_hide_finished_and_cancelled_events() -> None:
    finished = make_event(
        "Old event",
        days=-1,
        category="Other",
        modality="virtual",
        city=None,
        is_free=None,
        tags=[],
    )
    cancelled = make_event(
        "Cancelled event",
        days=1,
        category="Other",
        modality="virtual",
        city=None,
        is_free=None,
        tags=[],
    )
    cancelled.status = "cancelled"

    assert filter_events([finished, cancelled], EventFilters(), now=NOW) == []

