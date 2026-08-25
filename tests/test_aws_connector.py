from datetime import UTC, datetime

from backend.connectors.aws import AWSConnector


def build_connector() -> AWSConnector:
    return AWSConnector(now=datetime(2026, 8, 25, tzinfo=UTC))


def aws_event(*, virtual: bool = True, peru: bool = False) -> dict[str, object]:
    tags: list[dict[str, object]] = [
        {
            "id": "GLOBAL#local-tags-series#first-party",
            "tagNamespaceId": "GLOBAL#local-tags-series",
            "name": "first-party",
        },
        {
            "id": "GLOBAL#aws-tech-category#cloud-foundations",
            "tagNamespaceId": "GLOBAL#aws-tech-category",
            "name": "Cloud Foundations",
        },
    ]
    if virtual:
        tags.append(
            {
                "id": "GLOBAL#aws-event-type#virtual",
                "tagNamespaceId": "GLOBAL#aws-event-type",
                "name": "virtual",
            }
        )
    if peru:
        tags.extend(
            [
                {
                    "id": "GLOBAL#local-tags-location#peru",
                    "tagNamespaceId": "GLOBAL#local-tags-location",
                    "name": "Peru",
                },
                {
                    "id": "GLOBAL#local-tags-location-city#lima",
                    "tagNamespaceId": "GLOBAL#local-tags-location-city",
                    "name": "lima",
                },
            ]
        )
    return {
        "item": {
            "id": "events#aws-cloud-workshop",
            "additionalFields": {
                "date": "2026-09-05",
                "time": "7:00 - 9:00 PM",
                "timeZone": "Peru Time",
                "title": "AWS Cloud Workshop",
                "bodyBack": "<p>A free hands-on AWS workshop.</p>",
                "location": "Lima Tech Hub" if peru else "Online",
                "ctaLink": "https://pages.awscloud.com/register",
            },
        },
        "tags": tags,
    }


def test_aws_normalizes_virtual_event() -> None:
    event = build_connector()._normalize_event(aws_event())

    assert event is not None
    assert event.source == "AWS"
    assert event.organization == "AWS"
    assert event.modality == "virtual"
    assert event.start_date.isoformat() == "2026-09-05T19:00:00-05:00"
    assert event.end_date is not None
    assert event.end_date.isoformat() == "2026-09-05T21:00:00-05:00"
    assert event.is_free is True
    assert event.event_type == "workshop"
    assert event.registration_url == "https://pages.awscloud.com/register"


def test_aws_keeps_peru_in_person_event() -> None:
    event = build_connector()._normalize_event(aws_event(virtual=False, peru=True))

    assert event is not None
    assert event.modality == "in_person"
    assert event.city == "Lima"
    assert event.country == "Peru"


def test_aws_filters_foreign_in_person_and_finished_events() -> None:
    assert build_connector()._normalize_event(aws_event(virtual=False)) is None

    finished = aws_event()
    finished["item"]["additionalFields"]["date"] = "2026-01-05"
    assert build_connector()._normalize_event(finished) is None


def test_aws_marks_conflicting_virtual_and_in_person_tags_as_hybrid() -> None:
    raw = aws_event()
    raw["tags"].append(
        {
            "id": "GLOBAL#aws-aws-events-event-session-type#in-person",
            "tagNamespaceId": "GLOBAL#aws-aws-events-event-session-type",
            "name": "In Person",
        }
    )

    event = build_connector()._normalize_event(raw)

    assert event is not None
    assert event.modality == "hybrid"

