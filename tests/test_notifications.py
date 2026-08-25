from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.config import ConfigurationError
from backend.notifications.config import get_digest_settings
from backend.notifications.gmail_sender import GmailSender
from backend.notifications.models import DigestEvent, DigestPreferences
from backend.notifications.renderer import build_subject, render_html, render_plain
from backend.notifications.repository import recipient_hash


NOW = datetime(2026, 8, 25, 13, 30, tzinfo=UTC)


def make_event(**overrides: object) -> DigestEvent:
    values: dict[str, object] = {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": "AWS AI Workshop",
        "slug": "aws-ai-workshop",
        "organization": "AWS User Group Perú",
        "category": "Artificial Intelligence",
        "tags": ("AWS", "AI", "Python"),
        "event_type": "Workshop",
        "start_date": datetime(2026, 8, 27, 0, 0, tzinfo=UTC),
        "modality": "in_person",
        "city": "Lima",
        "is_free": True,
        "registration_url": "https://example.com/register",
        "source_url": "https://example.com/event",
        "source": "AWS",
        "first_seen_at": NOW,
    }
    values.update(overrides)
    return DigestEvent(**values)  # type: ignore[arg-type]


def test_preferences_combine_dimensions_and_match_any_tag_or_keyword() -> None:
    preferences = DigestPreferences(
        categories=frozenset({"Artificial Intelligence"}),
        tags=frozenset({"Cloud", "AWS"}),
        cities=frozenset({"Lima"}),
        modalities=frozenset({"in_person"}),
        keywords=frozenset({"bedrock", "python"}),
        free_only=True,
    )

    assert preferences.matches(make_event())
    assert not preferences.matches(make_event(city="Arequipa"))
    assert not preferences.matches(make_event(is_free=False))


def test_renderer_escapes_provider_content_and_adds_public_detail_link() -> None:
    event = make_event(title="AI <script>alert(1)</script>")

    html = render_html([event], site_url="https://recopilar-link.pages.dev")
    plain = render_plain([event], site_url="https://recopilar-link.pages.dev")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "?event=aws-ai-workshop" in html
    assert "?event=aws-ai-workshop" in plain
    assert build_subject([event], now=NOW).startswith("TechEvents Perú: 1 evento nuevo")


def test_recipient_hash_is_normalized_and_does_not_reveal_email() -> None:
    first = recipient_hash(" Person@Example.com ")
    second = recipient_hash("person@example.com")

    assert first == second
    assert len(first) == 64
    assert "person" not in first


def test_digest_settings_parse_preferences_and_strip_password_spaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("backend.notifications.config.load_dotenv", lambda: False)
    monkeypatch.setenv("GMAIL_SENDER_EMAIL", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAILS", "one@example.com, two@example.com")
    monkeypatch.setenv("DIGEST_TAGS", "AWS, AI")
    monkeypatch.setenv("DIGEST_MODALITIES", "virtual,hybrid")
    monkeypatch.setenv("DIGEST_FREE_ONLY", "true")

    settings = get_digest_settings()

    assert settings.app_password == "abcdefghijklmnop"
    assert settings.recipients == ("one@example.com", "two@example.com")
    assert settings.preferences.tags == frozenset({"AWS", "AI"})
    assert settings.preferences.free_only is True


def test_digest_settings_reject_invalid_modality(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backend.notifications.config.load_dotenv", lambda: False)
    monkeypatch.setenv("GMAIL_SENDER_EMAIL", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcdefghijklmnop")
    monkeypatch.setenv("DIGEST_RECIPIENT_EMAILS", "one@example.com")
    monkeypatch.setenv("DIGEST_MODALITIES", "telepathy")

    with pytest.raises(ConfigurationError, match="DIGEST_MODALITIES"):
        get_digest_settings()


@patch("backend.notifications.gmail_sender.smtplib.SMTP_SSL")
def test_gmail_sender_uses_ssl_login_and_multipart_message(
    smtp_ssl: MagicMock,
) -> None:
    connection = smtp_ssl.return_value.__enter__.return_value
    sender = GmailSender(
        sender_email="sender@gmail.com", app_password="abcdefghijklmnop"
    )

    sender.send(
        recipient="person@example.com",
        subject="Daily digest",
        plain_body="Plain",
        html_body="<strong>HTML</strong>",
    )

    connection.login.assert_called_once_with("sender@gmail.com", "abcdefghijklmnop")
    message = connection.send_message.call_args.args[0]
    assert message.is_multipart()
    assert message["To"] == "person@example.com"

