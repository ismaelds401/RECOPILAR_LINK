"""Validate read access and, optionally, backend write access to Supabase."""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from postgrest.exceptions import APIError

from backend.config import ConfigurationError
from backend.services.supabase_service import create_backend_client


def check_read(client: object) -> int:
    response = client.table("events").select("id", count="exact").limit(1).execute()
    return response.count or 0


def check_write(client: object) -> None:
    """Insert and remove a uniquely identified test row created by this script."""
    token = uuid4().hex
    event_hash = hashlib.sha256(f"connection-test:{token}".encode()).hexdigest()
    now = datetime.now(UTC)
    payload = {
        "title": "Supabase connection test",
        "slug": f"supabase-connection-test-{token[:12]}",
        "organization": "TechEvents Peru",
        "category": "Other",
        "event_type": "test",
        "start_date": (now + timedelta(days=1)).isoformat(),
        "timezone": "America/Lima",
        "modality": "virtual",
        "country": "Peru",
        "is_free": True,
        "source_url": "https://example.com/connection-test",
        "source": "connection-test",
        "source_event_id": token,
        "event_hash": event_hash,
        "status": "draft",
    }

    inserted = client.table("events").insert(payload).execute()
    if not inserted.data:
        raise RuntimeError("Supabase returned no inserted row.")

    client.table("events").delete().eq("event_hash", event_hash).execute()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-test",
        action="store_true",
        help="Insert and immediately delete one draft test event.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        client = create_backend_client()
        total = check_read(client)
        print(f"OK: connection and SELECT succeeded. Events found: {total}.")
        if args.write_test:
            check_write(client)
            print("OK: INSERT and DELETE succeeded; the test row was removed.")
        return 0
    except ConfigurationError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
    except APIError as exc:
        print(f"SUPABASE API ERROR: {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"CONNECTION ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
