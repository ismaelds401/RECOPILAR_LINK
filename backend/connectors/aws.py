"""AWS connector using the public JSON catalog behind the official events page."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.connectors.base_connector import (
    BaseConnector,
    ConnectorError,
    SourceDefinition,
)
from backend.models.event import Event
from backend.utils.text import build_event_hash, build_slug, infer_event_type, normalize_text

API_URL = "https://aws.amazon.com/api/dirs/items/search"
CATALOG_URL = "https://aws.amazon.com/events/explore-aws-events/"
DIRECTORY_ID = "alias#events-webinars-interactive-cards"
FIRST_PARTY_TAG = "GLOBAL#local-tags-series#first-party"
AMERICAS_TAG = "GLOBAL#local-tags-location#americas"
VIRTUAL_TAG = "GLOBAL#aws-event-type#virtual"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_ITEMS = 1000


class AWSConnector(BaseConnector):
    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        now: datetime | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.source = SourceDefinition(
            name="AWS Events",
            base_url=CATALOG_URL,
            source_type="API",
            connector="aws_events_catalog",
            priority=30,
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
        raw_by_id: dict[str, dict[str, object]] = {}
        for scope_tag in (VIRTUAL_TAG, AMERICAS_TAG):
            for raw in self._fetch_scope(scope_tag):
                item = raw.get("item")
                if isinstance(item, dict) and item.get("id"):
                    raw_by_id[str(item["id"])] = raw

        events = [self._normalize_event(raw) for raw in raw_by_id.values()]
        return sorted(
            (event for event in events if event is not None),
            key=lambda event: event.start_date,
        )

    def _fetch_scope(self, scope_tag: str) -> list[dict[str, object]]:
        params = [
            ("item.directoryId", DIRECTORY_ID),
            ("item.locale", "en_US"),
            ("tags.id", FIRST_PARTY_TAG),
            ("tags.id", scope_tag),
            ("sort_by", "item.additionalFields.date"),
            ("sort_order", "asc"),
            ("size", str(MAX_ITEMS)),
        ]
        try:
            response = self.session.get(
                API_URL, params=params, timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"AWS catalog request failed: {exc}") from exc
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ConnectorError("AWS catalog response exceeded the 5 MB safety limit.")
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ConnectorError("AWS catalog returned non-JSON content.")
        try:
            payload = response.json()
        except requests.JSONDecodeError as exc:
            raise ConnectorError(f"AWS catalog returned invalid JSON: {exc}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise ConnectorError("AWS catalog returned an unexpected JSON structure.")
        metadata = payload.get("metadata")
        if isinstance(metadata, dict) and int(metadata.get("totalHits") or 0) > MAX_ITEMS:
            raise ConnectorError("AWS catalog exceeded the 1000-item safety limit.")
        return [item for item in payload["items"] if isinstance(item, dict)]

    def _normalize_event(self, raw: dict[str, object]) -> Event | None:
        item = raw.get("item")
        if not isinstance(item, dict):
            return None
        fields = item.get("additionalFields")
        if not isinstance(fields, dict):
            return None
        title = str(fields.get("title") or fields.get("heading") or "").strip()
        source_event_id = str(item.get("id") or "").strip()
        if not title or not source_event_id or not fields.get("date"):
            return None

        tag_rows = raw.get("tags") or []
        tags = [tag for tag in tag_rows if isinstance(tag, dict)]
        tag_ids = {str(tag.get("id") or "") for tag in tags}
        tag_names = [str(tag.get("name") or "").strip() for tag in tags]
        modality = self._modality(tag_ids)
        searchable = normalize_text(
            " ".join(
                [title, *(tag_ids), *(tag_names), str(fields.get("location") or "")]
            )
        )
        is_peru = "peru" in searchable or "lima" in searchable
        if modality == "in_person" and not is_peru:
            return None

        description_html = str(fields.get("bodyBack") or fields.get("body") or "")
        description = self._plain_text(description_html)
        try:
            start_date, end_date, timezone_name = self._parse_dates(fields)
        except ValueError as exc:
            raise ConnectorError(
                f"AWS event {source_event_id} has an invalid date: {exc}"
            ) from exc
        if (end_date or start_date).astimezone(UTC) < self.now:
            return None

        registration_url = self._safe_url(
            str(fields.get("primaryCTALink") or fields.get("ctaLink") or "")
        )
        city = self._city(tags)
        country = "Peru" if is_peru else None
        venue = str(fields.get("location") or "").strip() or None
        public_tags = self._public_tags(tags)
        free_text = normalize_text(
            " ".join(
                [
                    str(fields.get("price") or ""),
                    str(fields.get("body") or ""),
                    description or "",
                ]
            )
        )
        is_free = (
            True
            if any(
                phrase in free_text
                for phrase in ("free", "no cost", "complimentary", "gratuito")
            )
            else None
        )
        event_hash = build_event_hash(title, start_date, "AWS", city)

        return Event(
            title=title,
            slug=build_slug(title, start_date, source_event_id),
            description=description,
            organization="AWS",
            category="Other",
            tags=public_tags,
            event_type=infer_event_type(title, public_tags),
            start_date=start_date,
            end_date=end_date,
            timezone=timezone_name,
            modality=modality,
            venue=venue,
            city=city,
            country=country,
            is_free=is_free,
            registration_url=registration_url,
            source_url=CATALOG_URL,
            image_url=self._safe_url(
                str(fields.get("mediaSrc") or fields.get("mediaThumbnail") or "")
            ),
            source="AWS",
            source_event_id=source_event_id,
            event_hash=event_hash,
            status="published",
        )

    @staticmethod
    def _modality(tag_ids: set[str]) -> str:
        virtual = VIRTUAL_TAG in tag_ids
        in_person = any(
            tag.endswith("#in-person")
            and "event-session-type" in tag
            for tag in tag_ids
        )
        if virtual and in_person:
            return "hybrid"
        if virtual:
            return "virtual"
        return "in_person"

    @staticmethod
    def _parse_dates(
        fields: dict[str, object],
    ) -> tuple[datetime, datetime | None, str]:
        day = date.fromisoformat(str(fields["date"]).strip())
        time_text = str(fields.get("time") or fields.get("body") or "")
        description = BeautifulSoup(
            str(fields.get("bodyBack") or ""), "html.parser"
        ).get_text(" ")
        timezone_text = str(fields.get("timeZone") or "") + " " + description
        timezone_name = AWSConnector._timezone_name(timezone_text)
        event_timezone = ZoneInfo(timezone_name)

        range_pattern = re.compile(
            r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?\s*"
            r"[-–—]\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM)(?!\w)",
            re.IGNORECASE,
        )
        range_match = range_pattern.search(time_text) or range_pattern.search(description)
        if range_match:
            end_period = range_match.group(6)
            start_time = AWSConnector._parts_time(
                range_match.group(1), range_match.group(2),
                range_match.group(3) or end_period,
            )
            end_time = AWSConnector._parts_time(
                range_match.group(4), range_match.group(5), end_period
            )
        else:
            matches = list(
                re.finditer(
                    r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(AM|PM)(?!\w)",
                    time_text or description,
                    re.IGNORECASE,
                )
            )
            start_time = (
                AWSConnector._matched_time(matches[0]) if matches else time(0)
            )
            end_time = (
                AWSConnector._matched_time(matches[1]) if len(matches) > 1 else None
            )
        start_date = datetime.combine(day, start_time, event_timezone)
        end_date = (
            datetime.combine(day, end_time, event_timezone) if end_time else None
        )
        return start_date, end_date, timezone_name

    @staticmethod
    def _matched_time(match: re.Match[str]) -> time:
        return AWSConnector._parts_time(
            match.group(1), match.group(2), match.group(3)
        )

    @staticmethod
    def _parts_time(hour_text: str, minute_text: str | None, period: str) -> time:
        hour = int(hour_text) % 12
        if period.upper() == "PM":
            hour += 12
        return time(hour, int(minute_text or 0))

    @staticmethod
    def _timezone_name(value: str) -> str:
        normalized = normalize_text(value)
        mappings = (
            (("peru", "lima", " pet "), "America/Lima"),
            (("pacific", " pst ", " pdt "), "America/Los_Angeles"),
            (("mountain", " mst ", " mdt "), "America/Denver"),
            (("central", " cst ", " cdt "), "America/Chicago"),
            (("eastern", " est ", " edt "), "America/New_York"),
            ((" utc ", " gmt "), "UTC"),
        )
        padded = f" {normalized} "
        for needles, timezone_name in mappings:
            if any(needle in padded for needle in needles):
                return timezone_name
        return "America/Lima"

    @staticmethod
    def _city(tags: list[dict[str, object]]) -> str | None:
        for tag in tags:
            namespace = str(tag.get("tagNamespaceId") or "")
            if namespace.endswith("location-city"):
                name = str(tag.get("name") or "").strip()
                return name.title() or None
        return None

    @staticmethod
    def _public_tags(tags: list[dict[str, object]]) -> list[str]:
        allowed = ("aws-tech-category", "aws-language", "aws-level")
        values = [
            str(tag.get("name") or "").strip()
            for tag in tags
            if any(part in str(tag.get("tagNamespaceId") or "") for part in allowed)
        ]
        return list(dict.fromkeys(value for value in values if value))

    @staticmethod
    def _plain_text(html: str) -> str | None:
        if not html:
            return None
        text = BeautifulSoup(html, "html.parser").get_text("\n")
        cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return cleaned or None

    @staticmethod
    def _safe_url(value: str) -> str | None:
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
        return None

