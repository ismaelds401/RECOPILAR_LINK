from datetime import UTC, datetime

from backend.models.event import Event
from backend.services.classifier import classify_event


def make_event(title: str, description: str | None = None) -> Event:
    return Event(
        title=title,
        slug="event",
        description=description,
        organization="Community",
        start_date=datetime(2026, 9, 5, 19, tzinfo=UTC),
        timezone="UTC",
        modality="virtual",
        source_url="https://example.com/event",
        source="Test",
        source_event_id="1",
        event_hash="a" * 64,
    )


def test_classifier_prioritizes_ai_over_cloud() -> None:
    event = classify_event(make_event("Generative AI with AWS Bedrock"))

    assert event.category == "Artificial Intelligence"
    assert "AI" in event.tags
    assert "AWS" in event.tags


def test_classifier_uses_description_and_preserves_source_tags() -> None:
    original = make_event("Engineering Meetup", "Kubernetes and Terraform workshop")
    original.tags = ["Community"]

    event = classify_event(original)

    assert event.category == "DevOps"
    assert event.tags[:2] == ["Community", "DevOps"]
    assert original.category == "Other"


def test_classifier_falls_back_to_other() -> None:
    event = classify_event(make_event("General community gathering"))

    assert event.category == "Other"
    assert "Other" not in event.tags


def test_classifier_prioritizes_title_over_generic_provider_tag() -> None:
    original = make_event("Cloud to Code")
    original.tags = ["Networking", "AI"]

    event = classify_event(original)

    assert event.category == "Cloud"


def test_classifier_understands_spanish_ai_abbreviation() -> None:
    event = classify_event(make_event("Construye un SaaS con IA"))

    assert event.category == "Artificial Intelligence"
    assert "AI" in event.tags


def test_classifier_prioritizes_react_native_as_mobile() -> None:
    event = classify_event(make_event("React Native y Expo para Hackathons"))

    assert event.category == "Mobile"
    assert "Mobile" in event.tags

