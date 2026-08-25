"""Verify that the Microsoft Reactor source ran and report safe aggregates."""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from backend.services.supabase_service import create_backend_client


def run() -> int:
    client = create_backend_client()
    sources = (
        client.table("event_sources")
        .select("id,name,enabled,last_scraped_at")
        .eq("connector", "microsoft_reactor_api")
        .limit(1)
        .execute()
        .data
    )
    if not sources:
        print("ERROR: Microsoft Reactor is not registered in event_sources.", file=sys.stderr)
        return 1
    source = sources[0]
    if source.get("enabled") is not True or not source.get("last_scraped_at"):
        print("ERROR: Microsoft Reactor has not completed a successful run.", file=sys.stderr)
        return 1

    logs = (
        client.table("scraping_logs")
        .select("status,events_found,events_inserted,events_updated,duplicates_found")
        .eq("source_id", source["id"])
        .order("started_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not logs or logs[0].get("status") != "success":
        print("ERROR: the latest Microsoft Reactor run was not successful.", file=sys.stderr)
        return 1

    upcoming = (
        client.table("events")
        .select("id", count="exact")
        .eq("source", "Microsoft Reactor")
        .eq("status", "published")
        .gte("start_date", datetime.now(UTC).isoformat())
        .execute()
    )
    log = logs[0]
    print("OK: Microsoft Reactor is enabled and its latest run succeeded.")
    print(
        "Latest run: "
        f"{log.get('events_found', 0)} found, "
        f"{log.get('events_inserted', 0)} inserted, "
        f"{log.get('events_updated', 0)} updated, "
        f"{log.get('duplicates_found', 0)} duplicates."
    )
    print(f"Upcoming published Microsoft Reactor events: {upcoming.count or 0}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

