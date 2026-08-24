from datetime import UTC, datetime

from backend.connectors.luma import LumaConnector


ICAL_FIXTURE = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Luma//Test//EN\r
BEGIN:VEVENT\r
DTSTART:20260905T000000Z\r
DTEND:20260905T020000Z\r
ORGANIZER;CN=Tech Peru:MAILTO:calendar-invite@lu.ma\r
UID:evt-lima@events.lu.ma\r
SUMMARY:[Lima] AI Hackathon\r
DESCRIPTION:Get up-to-date information at: https://luma.com/lima-ai\\n\\nAddress:\\nUTEC\\nBarranco\\, Peru\\n\\nHosted by Tech Peru\r
LOCATION:UTEC\\, Barranco\\, Peru\r
GEO:-12.135;-77.022\r
STATUS:CONFIRMED\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART:20260906T000000Z\r
DTEND:20260906T010000Z\r
ORGANIZER;CN=Virtual Builders:MAILTO:calendar-invite@lu.ma\r
UID:evt-virtual@events.lu.ma\r
SUMMARY:Serverless Workshop\r
DESCRIPTION:Get up-to-date information at: https://luma.com/serverless\\n\\nHosted by Virtual Builders\r
LOCATION:https://luma.com/event/evt-virtual\r
STATUS:TENTATIVE\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART:20260907T000000Z\r
DTEND:20260907T010000Z\r
ORGANIZER;CN=Foreign Builders:MAILTO:calendar-invite@lu.ma\r
UID:evt-foreign@events.lu.ma\r
SUMMARY:Bogota Developer Meetup\r
DESCRIPTION:Get up-to-date information at: https://luma.com/bogota\\n\\nHosted by Foreign Builders\r
LOCATION:Bogota\\, Colombia\r
GEO:4.711;-74.072\r
STATUS:CONFIRMED\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART:20260908T000000Z\r
DTEND:20260908T010000Z\r
ORGANIZER;CN=Hidden Foreign Event:MAILTO:calendar-invite@lu.ma\r
UID:evt-hidden-foreign@events.lu.ma\r
SUMMARY:[Bogota] Full Day Hackathon\r
DESCRIPTION:Get up-to-date information at: https://luma.com/bogota-hidden\\n\\nHosted by Hidden Foreign Event\r
LOCATION:https://luma.com/event/evt-hidden-foreign\r
STATUS:CONFIRMED\r
END:VEVENT\r
END:VCALENDAR\r
"""


def build_connector() -> LumaConnector:
    return LumaConnector(
        "cal-HBdmsARYSzYhpuc",
        "hack0",
        "Hack0 Community",
        now=datetime(2026, 8, 24, tzinfo=UTC),
    )


def test_luma_normalizes_peru_and_virtual_events() -> None:
    events = build_connector().parse(ICAL_FIXTURE)

    assert [event.source_event_id for event in events] == ["evt-lima", "evt-virtual"]
    assert events[0].city == "Lima"
    assert events[0].country == "Peru"
    assert events[0].modality == "in_person"
    assert events[0].event_type == "hackathon"
    assert events[1].country is None
    assert events[1].modality == "virtual"
    assert events[1].registration_url == "https://luma.com/serverless"


def test_luma_filters_past_events() -> None:
    connector = LumaConnector(
        "cal-HBdmsARYSzYhpuc",
        "hack0",
        "Hack0 Community",
        now=datetime(2027, 1, 1, tzinfo=UTC),
    )
    assert connector.parse(ICAL_FIXTURE) == []

