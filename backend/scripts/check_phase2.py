"""Verify that the first real Luma source and its events reached Supabase."""

from __future__ import annotations

import sys

from backend.services.supabase_service import create_backend_client


CONNECTOR = "luma_ical_hack0"


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
        print("ERROR: Luma source was not found.", file=sys.stderr)
        return 1

    source = sources[0]
    events_response = (
        client.table("events")
        .select("id", count="exact")
        .eq("source", "Luma")
        .execute()
    )
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
        print("ERROR: latest Luma scraping log is not successful.", file=sys.stderr)
        return 1

    print(f"OK source: {source['name']} ({source['source_type']}).")
    print(f"OK Luma events in Supabase: {events_response.count or 0}.")
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


