from datetime import UTC, datetime

from backend.connectors.microsoft_reactor import MicrosoftReactorConnector


def build_connector() -> MicrosoftReactorConnector:
    return MicrosoftReactorConnector(now=datetime(2026, 8, 25, tzinfo=UTC))


def reactor_event(
    *,
    livestream: bool = True,
    in_person: bool = False,
    location: str = "Redmond",
) -> dict[str, object]:
    formats = []
    if livestream:
        formats.append("Livestream")
    if in_person:
        formats.append("In person")
    return {
        "id": "27475",
        "title": "Build AI Apps with GitHub Copilot",
        "description": "A free practical tutorial.",
        "startDateTimeUtc": "2026-08-26T16:00:00Z",
        "endDateTimeUtc": "2026-08-26T17:00:00Z",
        "eventTopic": "AI Applications",
        "formats": formats,
        "contentLevel": "Intermediate",
        "eventType": {"id": 18, "name": "Tutorial"},
        "languages": ["English"],
        "location": location,
        "regions": ["North America"],
        "hasLivestreamSession": livestream,
        "hasInPersonSession": in_person,
        "isHybrid": livestream and in_person,
        "isSeries": False,
        "isTestEvent": False,
        "primaryRegistrationUrl": (
            "https://developer.microsoft.com/reactor/events/27475"
        ),
    }


def test_reactor_normalizes_global_livestream() -> None:
    event = build_connector()._normalize_event(reactor_event())

    assert event is not None
    assert event.source == "Microsoft Reactor"
    assert event.organization == "Microsoft Reactor"
    assert event.modality == "virtual"
    assert event.start_date.isoformat() == "2026-08-26T16:00:00+00:00"
    assert event.city is None
    assert event.country is None
    assert event.is_free is True
    assert event.event_type == "tutorial"
    assert "AI Applications" in event.tags


def test_reactor_keeps_peru_in_person_and_hybrid_events() -> None:
    in_person = build_connector()._normalize_event(
        reactor_event(livestream=False, in_person=True, location="Lima, Peru")
    )
    hybrid = build_connector()._normalize_event(
        reactor_event(livestream=True, in_person=True, location="Lima, Peru")
    )

    assert in_person is not None
    assert in_person.modality == "in_person"
    assert in_person.city == "Lima, Peru"
    assert in_person.country == "Peru"
    assert hybrid is not None
    assert hybrid.modality == "hybrid"


def test_reactor_filters_foreign_in_person_finished_series_and_tests() -> None:
    assert (
        build_connector()._normalize_event(
            reactor_event(livestream=False, in_person=True, location="Redmond")
        )
        is None
    )

    finished = reactor_event()
    finished["startDateTimeUtc"] = "2026-01-01T00:00:00Z"
    finished["endDateTimeUtc"] = "2026-01-01T01:00:00Z"
    assert build_connector()._normalize_event(finished) is None

    series = reactor_event()
    series["isSeries"] = True
    assert build_connector()._normalize_event(series) is None

    test_event = reactor_event()
    test_event["isTestEvent"] = True
    assert build_connector()._normalize_event(test_event) is None


def test_reactor_falls_back_to_official_detail_url() -> None:
    raw = reactor_event()
    raw["primaryRegistrationUrl"] = "javascript:alert(1)"

    event = build_connector()._normalize_event(raw)

    assert event is not None
    assert event.registration_url == (
        "https://developer.microsoft.com/reactor/events/27475/"
    )

