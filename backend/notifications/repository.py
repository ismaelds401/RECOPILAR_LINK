"""Supabase access for digest candidates and delivery tracking."""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime, timedelta

from supabase import Client

from backend.notifications.models import DigestEvent


EVENT_COLUMNS = (
    "id,title,slug,organization,category,tags,event_type,start_date,modality,"
    "city,is_free,registration_url,source_url,source,first_seen_at"
)


def recipient_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


class DigestRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    def fetch_recent_events(
        self, *, now: datetime, lookback_hours: int
    ) -> list[DigestEvent]:
        current = now.astimezone(UTC)
        since = current - timedelta(hours=lookback_hours)
        rows = (
            self.client.table("events")
            .select(EVENT_COLUMNS)
            .eq("status", "published")
            .gte("first_seen_at", since.isoformat())
            .gte("start_date", current.isoformat())
            .order("start_date")
            .limit(500)
            .execute()
            .data
        )
        return [DigestEvent.from_database_row(row) for row in rows]

    def delivery_statuses(
        self, *, email: str, event_ids: list[str]
    ) -> dict[str, str]:
        if not event_ids:
            return {}
        rows = (
            self.client.table("notification_deliveries")
            .select("event_id,status")
            .eq("recipient_hash", recipient_hash(email))
            .in_("event_id", event_ids)
            .execute()
            .data
        )
        return {str(row["event_id"]): str(row["status"]) for row in rows}

    def claim(
        self, *, email: str, events: list[DigestEvent], digest_date: date
    ) -> list[DigestEvent]:
        statuses = self.delivery_statuses(
            email=email, event_ids=[event.id for event in events]
        )
        claimable = [
            event
            for event in events
            if statuses.get(event.id) != "sent"
        ]
        if not claimable:
            return []
        attempted_at = datetime.now(UTC).isoformat()
        payload = [
            {
                "recipient_hash": recipient_hash(email),
                "event_id": event.id,
                "digest_date": digest_date.isoformat(),
                "status": "pending",
                "attempted_at": attempted_at,
                "sent_at": None,
                "error_message": None,
            }
            for event in claimable
        ]
        self.client.table("notification_deliveries").upsert(
            payload, on_conflict="recipient_hash,event_id"
        ).execute()
        return claimable

    def mark_sent(self, *, email: str, event_ids: list[str]) -> None:
        if not event_ids:
            return
        (
            self.client.table("notification_deliveries")
            .update(
                {
                    "status": "sent",
                    "sent_at": datetime.now(UTC).isoformat(),
                    "error_message": None,
                }
            )
            .eq("recipient_hash", recipient_hash(email))
            .in_("event_id", event_ids)
            .execute()
        )

    def mark_failed(self, *, email: str, event_ids: list[str], error: str) -> None:
        if not event_ids:
            return
        (
            self.client.table("notification_deliveries")
            .update(
                {
                    "status": "failed",
                    "sent_at": None,
                    "error_message": error[:1000],
                }
            )
            .eq("recipient_hash", recipient_hash(email))
            .in_("event_id", event_ids)
            .execute()
        )

