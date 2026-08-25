from datetime import UTC, datetime

from backend.connectors.gdg import GDGChapter, GDGConnector


def build_connector() -> GDGConnector:
    return GDGConnector(
        GDGChapter(565, "gdg-lima", "GDG Lima", "Lima"),
        now=datetime(2026, 8, 25, tzinfo=UTC),
    )


def test_gdg_normalizes_public_event_fields() -> None:
    raw = {
        "id": 129078,
        "title": "GDG Lima Meetup - Agosto 2026",
        "start_date": "2026-08-31T23:00:00Z",
        "end_date": "2026-09-01T02:00:00Z",
        "event_timezone": "America/Lima",
        "audience_type": "IN_PERSON",
        "is_virtual_event": False,
        "is_hidden": False,
        "relative_url": (
            "/events/details/google-gdg-lima-presents-"
            "gdg-lima-meetup-agosto-2026/"
        ),
        "description": "<p>Aprende <strong>Google Cloud</strong>.</p>",
        "cropped_banner_url": "https://images.example.com/banner.png",
        "custom_tickets_url": "",
        "venue_name": "Torre KPMG",
        "venue_address": "444 Avenida Javier Prado Este",
        "venue_city": "San Isidro",
        "venue_state": "Provincia de Lima",
        "event_type_title": "Free registration",
        "tags": ["Tech Talk / Meetup"],
        "chapter_title": "GDG Lima",
    }

    event = build_connector()._normalize_event(raw)

    assert event is not None
    assert event.source == "GDG"
    assert event.source_event_id == "129078"
    assert event.start_date.isoformat() == "2026-08-31T18:00:00-05:00"
    assert event.modality == "in_person"
    assert event.city == "Lima"
    assert event.country == "Peru"
    assert event.is_free is True
    assert event.event_type == "meetup"
    assert event.description == "Aprende\nGoogle Cloud\n."
    assert event.venue is not None and "Torre KPMG" in event.venue
    assert event.registration_url == event.source_url


def test_gdg_recognizes_virtual_event_and_external_registration() -> None:
    raw = {
        "id": 130000,
        "title": "Gemini Workshop",
        "start_date": "2026-09-10T23:00:00Z",
        "end_date": "2026-09-11T00:00:00Z",
        "event_timezone": "America/Lima",
        "audience_type": "VIRTUAL",
        "is_virtual_event": True,
        "is_hidden": False,
        "static_url": "https://gdg.community.dev/e/example/",
        "description_short": "Evento online",
        "custom_tickets_url": "https://tickets.example.com/gemini",
        "event_type_title": "External registration",
        "tags": ["Workshop / Study Group"],
        "chapter_title": "GDG Lima",
    }

    event = build_connector()._normalize_event(raw)

    assert event is not None
    assert event.modality == "virtual"
    assert event.registration_url == "https://tickets.example.com/gemini"
    assert event.is_free is None
    assert event.event_type == "workshop"


def test_gdg_filters_hidden_and_finished_events() -> None:
    base = {
        "id": 1,
        "title": "Old event",
        "start_date": "2026-01-01T00:00:00Z",
        "end_date": "2026-01-01T01:00:00Z",
        "is_hidden": False,
    }
    assert build_connector()._normalize_event(base) is None

    hidden = {
        "id": 2,
        "title": "Hidden event",
        "start_date": "2026-10-01T00:00:00Z",
        "is_hidden": True,
    }
    assert build_connector()._normalize_event(hidden) is None


