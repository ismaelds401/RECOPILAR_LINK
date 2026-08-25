"""Verify the AWS source, events, provider IDs, and latest log in Supabase."""

from __future__ import annotations

import sys

from backend.services.supabase_service import create_backend_client


CONNECTOR = "aws_events_catalog"


def main() -> int:
    client = create_backend_client()
    sources = (
        client.table("event_sources")
        .select("id,name,source_type,last_scraped_at")
        .eq("connector", CONNECTOR)
        .limit(1)
        .execute()
        .data
    )
    if not sources:
        print("ERROR: AWS source was not found.", file=sys.stderr)
        return 1

    source = sources[0]
    events = (
        client.table("events")
        .select("id,source_event_id", count="exact")
        .eq("source", "AWS")
        .execute()
    )
    rows = events.data or []
    provider_ids = [row.get("source_event_id") for row in rows]
    if not rows:
        print("ERROR: no AWS event was found in Supabase.", file=sys.stderr)
        return 1
    if None in provider_ids or len(provider_ids) != len(set(provider_ids)):
        print("ERROR: AWS provider-ID deduplication failed.", file=sys.stderr)
        return 1

    logs = (
        client.table("scraping_logs")
        .select(
            "status,events_found,events_inserted,events_updated,"
            "duplicates_found,finished_at,error_message"
        )
        .eq("source_id", source["id"])
        .order("started_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not logs or logs[0]["status"] != "success":
        print("ERROR: latest AWS scraping log is not successful.", file=sys.stderr)
        return 1

    print(f"OK source: {source['name']} ({source['source_type']}).")
    print(f"OK AWS events in Supabase: {events.count or 0} unique provider IDs.")
    print(
        "OK latest log: "
        f"found={logs[0]['events_found']}, "
        f"inserted={logs[0]['events_inserted']}, "
        f"updated={logs[0]['events_updated']}, "
        f"duplicates={logs[0]['duplicates_found']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

