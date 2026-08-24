"""Idempotent Supabase persistence for normalized events and run logs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from supabase import Client

from backend.connectors.base_connector import SourceDefinition
from backend.models.event import Event


@dataclass(slots=True)
class PersistenceStats:
    found: int = 0
    inserted: int = 0
    updated: int = 0
    duplicates: int = 0


class EventRepository:
    def __init__(self, client: Client) -> None:
        self.client = client

    def ensure_source(self, source: SourceDefinition) -> str:
        existing = (
            self.client.table("event_sources")
            .select("id")
            .eq("connector", source.connector)
            .limit(1)
            .execute()
            .data
        )
        payload = {
            "name": source.name,
            "base_url": source.base_url,
            "source_type": source.source_type,
            "connector": source.connector,
            "priority": source.priority,
            "enabled": True,
        }
        if existing:
            source_id = existing[0]["id"]
            self.client.table("event_sources").update(payload).eq(
                "id", source_id
            ).execute()
            return str(source_id)

        created = self.client.table("event_sources").insert(payload).execute().data
        if not created:
            raise RuntimeError("Supabase did not return the created event source.")
        return str(created[0]["id"])

    def start_log(self, source_id: str) -> int:
        created = (
            self.client.table("scraping_logs")
            .insert({"source_id": source_id, "status": "running"})
            .execute()
            .data
        )
        if not created:
            raise RuntimeError("Supabase did not return the created scraping log.")
        return int(created[0]["id"])

    def finish_log(
        self,
        log_id: int,
        status: str,
        stats: PersistenceStats,
        error_message: str | None = None,
    ) -> None:
        self.client.table("scraping_logs").update(
            {
                "finished_at": datetime.now(UTC).isoformat(),
                "status": status,
                "events_found": stats.found,
                "events_inserted": stats.inserted,
                "events_updated": stats.updated,
                "duplicates_found": stats.duplicates,
                "error_message": error_message[:4000] if error_message else None,
            }
        ).eq("id", log_id).execute()

    def persist(self, events: list[Event]) -> PersistenceStats:
        stats = PersistenceStats(found=len(events))
        seen_hashes: set[str] = set()
        unique_events: list[Event] = []
        for event in events:
            if event.event_hash in seen_hashes:
                stats.duplicates += 1
                continue
            seen_hashes.add(event.event_hash)
            unique_events.append(event)

        existing_source_rows = (
            self.client.table("events")
            .select("id,source_event_id,event_hash")
            .eq("source", "Luma")
            .execute()
            .data
        )
        by_source_id = {
            row["source_event_id"]: row
            for row in existing_source_rows
            if row.get("source_event_id")
        }

        new_hashes = [
            event.event_hash
            for event in unique_events
            if event.source_event_id not in by_source_id
        ]
        existing_hash_rows: list[dict[str, object]] = []
        for batch in self._chunks(new_hashes, 100):
            existing_hash_rows.extend(
                self.client.table("events")
                .select("id,event_hash")
                .in_("event_hash", batch)
                .execute()
                .data
            )
        by_hash = {str(row["event_hash"]): row for row in existing_hash_rows}

        inserts: list[dict[str, object]] = []
        updates: list[dict[str, object]] = []
        observed_at = datetime.now(UTC).isoformat()
        for event in unique_events:
            payload = event.to_database_payload()
            payload["last_seen_at"] = observed_at
            existing_source_event = by_source_id.get(event.source_event_id)
            if existing_source_event:
                payload["id"] = existing_source_event["id"]
                updates.append(payload)
                continue
            if event.event_hash in by_hash:
                stats.duplicates += 1
                continue
            inserts.append(payload)

        for batch in self._chunks(updates, 100):
            self.client.table("events").upsert(batch, on_conflict="id").execute()
        for batch in self._chunks(inserts, 100):
            self.client.table("events").insert(batch).execute()

        stats.updated += len(updates)
        stats.inserted += len(inserts)
        return stats

    @staticmethod
    def _chunks(values: list, size: int) -> list[list]:
        return [values[index : index + size] for index in range(0, len(values), size)]

    def mark_source_scraped(self, source_id: str) -> None:
        self.client.table("event_sources").update(
            {"last_scraped_at": datetime.now(UTC).isoformat()}
        ).eq("id", source_id).execute()

