"""Verify the Phase 9 delivery table and report safe aggregate information."""

from __future__ import annotations

from collections import Counter

from backend.services.supabase_service import create_backend_client


def run() -> int:
    client = create_backend_client()
    rows = (
        client.table("notification_deliveries")
        .select("status,digest_date")
        .order("attempted_at", desc=True)
        .limit(100)
        .execute()
        .data
    )
    counts = Counter(str(row["status"]) for row in rows)
    print("OK: notification_deliveries is accessible to the backend.")
    print(
        "Recent delivery rows: "
        f"{len(rows)} total, {counts['sent']} sent, "
        f"{counts['pending']} pending, {counts['failed']} failed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

