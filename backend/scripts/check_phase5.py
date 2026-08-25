"""Verify classification and fuzzy deduplication over stored Supabase events."""

from __future__ import annotations

import sys
from collections import Counter
from datetime import UTC, datetime

from backend.services.deduplicator import (
    DuplicateCandidate,
    candidates_are_probable_duplicates,
)
from backend.services.supabase_service import create_backend_client


def main() -> int:
    client = create_backend_client()
    rows = (
        client.table("events")
        .select("id,title,start_date,organization,city,source,category,tags")
        .eq("status", "published")
        .gte("start_date", datetime.now(UTC).isoformat())
        .order("start_date")
        .execute()
        .data
    )
    if not rows:
        print("ERROR: no upcoming published events were found.", file=sys.stderr)
        return 1

    categories = Counter(str(row.get("category") or "Other") for row in rows)
    classified = sum(count for name, count in categories.items() if name != "Other")
    tagged = sum(bool(row.get("tags")) for row in rows)
    if classified == 0:
        print("ERROR: no event received an automatic category.", file=sys.stderr)
        return 1
    if tagged == 0:
        print("ERROR: no event has filterable tags.", file=sys.stderr)
        return 1

    candidates = [DuplicateCandidate.from_database_row(row) for row in rows]
    duplicate_pairs: list[tuple[str, str]] = []
    for index, first in enumerate(candidates):
        for second in candidates[index + 1 :]:
            if first.source == second.source:
                continue
            if candidates_are_probable_duplicates(first, second):
                duplicate_pairs.append((first.title, second.title))
    if duplicate_pairs:
        print(
            f"ERROR: {len(duplicate_pairs)} probable cross-source duplicates remain.",
            file=sys.stderr,
        )
        for first, second in duplicate_pairs:
            print(f"- {first} <> {second}", file=sys.stderr)
        return 1

    distribution = ", ".join(
        f"{name}={count}" for name, count in categories.most_common()
    )
    print(f"OK upcoming published events: {len(rows)}.")
    print(f"OK automatically classified events: {classified}.")
    print(f"OK events with filterable tags: {tagged}.")
    print(f"OK category distribution: {distribution}.")
    print("OK probable cross-source duplicates: 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

