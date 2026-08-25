"""Build and optionally send the daily TechEvents Peru Gmail digest."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from backend.notifications.config import get_digest_settings
from backend.notifications.gmail_sender import GmailSender
from backend.notifications.renderer import build_subject, render_html, render_plain
from backend.notifications.repository import DigestRepository
from backend.services.supabase_service import create_backend_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Query and filter events without claiming deliveries or sending email.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=10,
        help="Maximum event titles to print; email addresses and secrets are never printed.",
    )
    return parser.parse_args()


def run() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    settings = get_digest_settings(require_gmail=not args.dry_run)
    now = datetime.now(UTC)
    repository = DigestRepository(create_backend_client())
    recent = repository.fetch_recent_events(
        now=now, lookback_hours=settings.lookback_hours
    )
    matching = [event for event in recent if settings.preferences.matches(event)]
    matching = matching[: settings.max_events]

    print(
        f"Digest candidates: {len(recent)} recent, {len(matching)} matching preferences."
    )
    for event in matching[: max(0, args.preview)]:
        print(f"- {event.start_date.isoformat()} | {event.title}")

    if args.dry_run:
        print("DRY RUN: no delivery rows created and no email sent.")
        return 0
    if not matching:
        print("No new matching events; no email sent.")
        return 0

    sender = GmailSender(
        sender_email=settings.sender_email,
        app_password=settings.app_password,
    )
    sent_count = 0
    failures = 0
    digest_date = now.astimezone(ZoneInfo("America/Lima")).date()
    for recipient in settings.recipients:
        events = repository.claim(
            email=recipient, events=matching, digest_date=digest_date
        )
        if not events:
            print("Recipient already has every matching event; no duplicate sent.")
            continue
        event_ids = [event.id for event in events]
        try:
            sender.send(
                recipient=recipient,
                subject=build_subject(events, now=now),
                plain_body=render_plain(events, site_url=settings.site_url),
                html_body=render_html(events, site_url=settings.site_url),
            )
            repository.mark_sent(email=recipient, event_ids=event_ids)
            sent_count += 1
            print(f"Digest sent successfully with {len(events)} events.")
        except Exception as exc:
            failures += 1
            repository.mark_failed(
                email=recipient,
                event_ids=event_ids,
                error=f"{type(exc).__name__}: {exc}",
            )
            print(
                f"ERROR sending digest: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )

    print(f"Digest result: {sent_count} sent, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())

