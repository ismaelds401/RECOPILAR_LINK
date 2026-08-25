"""Run the event collection pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from backend.connectors.base_connector import BaseConnector
from backend.connectors.aws import AWSConnector
from backend.connectors.gdg import GDGConnector, INITIAL_GDG_CHAPTERS
from backend.connectors.luma import LumaConnector
from backend.connectors.microsoft_reactor import MicrosoftReactorConnector
from backend.services.event_repository import EventRepository, PersistenceStats
from backend.services.classifier import classify_events
from backend.services.supabase_service import create_backend_client


def build_connectors() -> list[BaseConnector]:
    connectors: list[BaseConnector] = [
        LumaConnector(
            calendar_id="cal-HBdmsARYSzYhpuc",
            calendar_slug="hack0",
            calendar_name="Hack0 Community",
        )
    ]
    connectors.extend(GDGConnector(chapter) for chapter in INITIAL_GDG_CHAPTERS)
    connectors.append(AWSConnector())
    connectors.append(MicrosoftReactorConnector())
    return connectors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and normalize events without connecting to Supabase.",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=5,
        help="Number of normalized event summaries to print.",
    )
    parser.add_argument(
        "--only",
        choices=("all", "luma", "gdg", "aws", "reactor"),
        default="all",
        help="Run every connector or only one provider family.",
    )
    return parser.parse_args()


def print_preview(events: list[object], limit: int) -> None:
    for event in events[: max(0, limit)]:
        print(
            json.dumps(
                {
                    "title": event.title,
                    "start_date": event.start_date.isoformat(),
                    "category": event.category,
                    "event_type": event.event_type,
                    "tags": event.tags,
                    "modality": event.modality,
                    "city": event.city,
                    "country": event.country,
                    "registration_url": event.registration_url,
                },
                ensure_ascii=False,
            )
        )


def run() -> int:
    # Windows PowerShell may default to a legacy code page. Never let an emoji
    # or accented event title abort an otherwise valid connector run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    connectors = build_connectors()
    if args.only != "all":
        provider = args.only.upper()
        connectors = [connector for connector in connectors if provider in connector.source.name.upper()]
    repository = None if args.dry_run else EventRepository(create_backend_client())
    failures = 0

    for connector in connectors:
        source_id: str | None = None
        log_id: int | None = None
        stats = PersistenceStats()
        try:
            if repository:
                source_id = repository.ensure_source(connector.source)
                log_id = repository.start_log(source_id)

            events = classify_events(connector.collect())
            print(f"{connector.source.name}: {len(events)} upcoming events normalized.")
            print_preview(events, args.preview)

            if repository:
                stats = repository.persist(events)
                repository.mark_source_scraped(source_id)
                repository.finish_log(log_id, "success", stats)
                print(
                    f"Supabase: {stats.inserted} inserted, {stats.updated} updated, "
                    f"{stats.duplicates} duplicates."
                )
        except Exception as exc:
            failures += 1
            print(
                f"ERROR [{connector.source.connector}]: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            if repository and log_id is not None:
                stats.found = stats.found or 0
                try:
                    repository.finish_log(log_id, "failed", stats, str(exc))
                except Exception as log_exc:
                    print(f"ERROR writing scraping log: {log_exc}", file=sys.stderr)

    return 1 if failures == len(connectors) else 0


if __name__ == "__main__":
    raise SystemExit(run())

