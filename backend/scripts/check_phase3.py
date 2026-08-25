"""Verify the GDG sources, unique events, and latest logs in Supabase."""

from __future__ import annotations

import sys

from backend.connectors.gdg import INITIAL_GDG_CHAPTERS
from backend.services.supabase_service import create_backend_client


EXPECTED_UNIQUE_EVENTS = 4
SHARED_EVENT_ID = "128726"


def main() -> int:
    client = create_backend_client()
    connectors = [
        f"gdg_api_{chapter.slug.replace('-', '_')}"
        for chapter in INITIAL_GDG_CHAPTERS
    ]
    sources = (
        client.table("event_sources")
        .select("id,name,connector,last_scraped_at")
        .in_("connector", connectors)
        .execute()
        .data
    )
    if len(sources) != len(connectors):
        found = {source["connector"] for source in sources}
        missing = sorted(set(connectors) - found)
        print(f"ERROR: missing GDG sources: {', '.join(missing)}", file=sys.stderr)
        return 1

    events = (
        client.table("events")
        .select("id,source_event_id", count="exact")
        .eq("source", "GDG")
        .execute()
    )
    event_rows = events.data or []
    source_event_ids = {
        row["source_event_id"] for row in event_rows if row.get("source_event_id")
    }
    shared_count = sum(
        row.get("source_event_id") == SHARED_EVENT_ID for row in event_rows
    )
    if events.count != EXPECTED_UNIQUE_EVENTS:
        print(
            f"ERROR: expected {EXPECTED_UNIQUE_EVENTS} GDG events, "
            f"found {events.count or 0}.",
            file=sys.stderr,
        )
        return 1
    if len(source_event_ids) != EXPECTED_UNIQUE_EVENTS or shared_count != 1:
        print("ERROR: GDG provider-ID deduplication failed.", file=sys.stderr)
        return 1

    for source in sources:
        logs = (
            client.table("scraping_logs")
            .select("status,events_found,events_inserted,events_updated,finished_at")
            .eq("source_id", source["id"])
            .order("started_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if not logs or logs[0]["status"] != "success":
            print(
                f"ERROR: latest log for {source['name']} is not successful.",
                file=sys.stderr,
            )
            return 1
        print(
            f"OK source: {source['name']}; "
            f"latest found={logs[0]['events_found']}, "
            f"inserted={logs[0]['events_inserted']}, "
            f"updated={logs[0]['events_updated']}."
        )

    print(f"OK GDG events in Supabase: {events.count} unique provider IDs.")
    print(f"OK shared event {SHARED_EVENT_ID}: exactly one stored row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

