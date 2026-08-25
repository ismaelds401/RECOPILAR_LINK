"""Microsoft Reactor connector using the public JSON events catalog."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.connectors.base_connector import (
    BaseConnector,
    ConnectorError,
    SourceDefinition,
)
from backend.models.event import Event
from backend.utils.text import build_event_hash, build_slug, infer_event_type, normalize_text

API_URL = "https://developer.microsoft.com/reactor/api/events"
CATALOG_URL = "https://developer.microsoft.com/en-us/reactor/"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20


class MicrosoftReactorConnector(BaseConnector):
    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        now: datetime | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.source = SourceDefinition(
            name="Microsoft Reactor",
            base_url=CATALOG_URL,
            source_type="API",
            connector="microsoft_reactor_api",
            priority=40,
        )
        self.session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "TechEventsPeru/0.1 "
                    "(+https://github.com/ismaelds401/RECOPILAR_LINK)"
                ),
                "Accept": "application/json",
            }
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def collect(self) -> list[Event]:
        raw_events: list[dict[str, object]] = []
        page = 1
        while page <= MAX_PAGES:
            payload = self._fetch_page(page)
            items = payload.get("items")
            if not isinstance(items, list):
                raise ConnectorError("Microsoft Reactor JSON has no items list.")
            raw_events.extend(item for item in items if isinstance(item, dict))

            try:
                total_pages = int(payload.get("totalPages") or 1)
            except (TypeError, ValueError) as exc:
                raise ConnectorError(
                    "Microsoft Reactor returned invalid pagination metadata."
                ) from exc
            if total_pages > MAX_PAGES:
                raise ConnectorError(
                    "Microsoft Reactor pagination exceeded the 20-page safety limit."
                )
            if page >= total_pages:
                break
            page += 1
        else:
            raise ConnectorError(
                "Microsoft Reactor pagination exceeded the 20-page safety limit."
            )

        events = [self._normalize_event(item) for item in raw_events]
        return sorted(
            (event for event in events if event is not None),
            key=lambda event: event.start_date,
        )

    def _fetch_page(self, page: int) -> dict[str, object]:
        params = {"page": page, "eventTypes": "individualEvents"}
        try:
            response = self.session.get(
                API_URL, params=params, timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"Microsoft Reactor request failed: {exc}") from exc
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ConnectorError(
                "Microsoft Reactor response exceeded the 5 MB safety limit."
            )
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ConnectorError("Microsoft Reactor returned non-JSON content.")
        try:
            payload = response.json()
        except requests.JSONDecodeError as exc:
            raise ConnectorError(
                f"Microsoft Reactor returned invalid JSON: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ConnectorError("Microsoft Reactor returned an unexpected JSON structure.")
        return payload

    def _normalize_event(self, raw: dict[str, object]) -> Event | None:
        title = str(raw.get("title") or "").strip()
        source_event_id = str(raw.get("id") or "").strip()
        if not title or not source_event_id or not raw.get("startDateTimeUtc"):
            return None
        if raw.get("isSeries") is True or raw.get("isTestEvent") is True:
            return None

        try:
            start_date = self._parse_datetime(str(raw["startDateTimeUtc"]))
            end_date = (
                self._parse_datetime(str(raw["endDateTimeUtc"]))
                if raw.get("endDateTimeUtc")
                else None
            )
        except ValueError as exc:
            raise ConnectorError(
                f"Microsoft Reactor event {source_event_id} has an invalid date: {exc}"
            ) from exc
        if (end_date or start_date) < self.now:
            return None

        modality = self._modality(raw)
        location_values = [
            str(raw.get(field) or "")
            for field in ("location", "locationDisplayAddress", "locationDisplayCity")
        ]
        regions = [str(value) for value in (raw.get("regions") or [])]
        location_search = normalize_text(" ".join([*location_values, *regions]))
        is_peru = "peru" in location_search or "lima" in location_search
        if modality == "in_person" and not is_peru:
            return None

        detail_url = f"https://developer.microsoft.com/reactor/events/{source_event_id}/"
        registration_url = self._safe_url(
            str(raw.get("primaryRegistrationUrl") or "")
        ) or detail_url
        formats = [str(value).strip() for value in (raw.get("formats") or [])]
        languages = [str(value).strip() for value in (raw.get("languages") or [])]
        event_type_value = raw.get("eventType")
        event_type_name = (
            str(event_type_value.get("name") or "").strip()
            if isinstance(event_type_value, dict)
            else ""
        )
        tags = self._unique_tags(
            [
                str(raw.get("eventTopic") or ""),
                str(raw.get("contentLevel") or ""),
                event_type_name,
                *formats,
                *languages,
            ]
        )
        city = (
            str(raw.get("locationDisplayCity") or raw.get("location") or "").strip()
            or None
        )
        if modality == "virtual":
            city = None
        venue = (
            str(raw.get("locationDisplayAddress") or raw.get("location") or "").strip()
            or None
        )
        if modality == "virtual":
            venue = None
        description = str(raw.get("description") or "").strip() or None
        free_search = normalize_text(f"{title} {description or ''}")
        is_free = (
            True
            if any(term in free_search for term in ("free", "gratuito", "sin costo"))
            else None
        )

        return Event(
            title=title,
            slug=build_slug(title, start_date, source_event_id),
            description=description,
            organization="Microsoft Reactor",
            category="Other",
            tags=tags,
            event_type=(
                normalize_text(event_type_name).replace(" ", "_")
                or infer_event_type(title, tags)
            ),
            start_date=start_date,
            end_date=end_date,
            timezone="UTC",
            modality=modality,
            venue=venue,
            city=city,
            country="Peru" if is_peru else None,
            is_free=is_free,
            registration_url=registration_url,
            source_url=detail_url,
            image_url=self._safe_url(str(raw.get("bannerImageUrl") or "")),
            source="Microsoft Reactor",
            source_event_id=source_event_id,
            event_hash=build_event_hash(
                title, start_date, "Microsoft Reactor", city
            ),
            status="published",
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _modality(raw: dict[str, object]) -> str:
        formats = normalize_text(" ".join(str(x) for x in (raw.get("formats") or [])))
        livestream = raw.get("hasLivestreamSession") is True or "livestream" in formats
        in_person = raw.get("hasInPersonSession") is True or "in person" in formats
        if raw.get("isHybrid") is True or (livestream and in_person):
            return "hybrid"
        if livestream:
            return "virtual"
        return "in_person"

    @staticmethod
    def _safe_url(value: str) -> str | None:
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        return None

    @staticmethod
    def _unique_tags(values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))

