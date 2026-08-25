"""Google Developer Groups connector using its public JSON event endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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

API_ROOT = "https://gdg.community.dev/api"
SITE_ROOT = "https://gdg.community.dev"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
EVENT_FIELDS = ",".join(
    (
        "id",
        "title",
        "start_date",
        "end_date",
        "event_timezone",
        "audience_type",
        "is_virtual_event",
        "is_hidden",
        "relative_url",
        "static_url",
        "description",
        "description_short",
        "cropped_banner_url",
        "cropped_picture_url",
        "custom_tickets_url",
        "cohost_registration_url",
        "venue_name",
        "venue_address",
        "venue_city",
        "venue_state",
        "venue_zip_code",
        "event_type_title",
        "tags",
        "chapter_title",
    )
)


@dataclass(frozen=True, slots=True)
class GDGChapter:
    id: int
    slug: str
    name: str
    city: str
    country: str = "Peru"


INITIAL_GDG_CHAPTERS = (
    GDGChapter(565, "gdg-lima", "GDG Lima", "Lima"),
    GDGChapter(395, "gdg-cloud-lima", "GDG Cloud Lima", "Lima"),
    GDGChapter(894, "gdg-open", "GDG Open", "Lima"),
    GDGChapter(1483, "gdg-callao", "GDG Callao", "Callao"),
)


class GDGConnector(BaseConnector):
    def __init__(
        self,
        chapter: GDGChapter,
        *,
        timeout_seconds: int = 20,
        now: datetime | None = None,
    ) -> None:
        self.chapter = chapter
        self.timeout_seconds = timeout_seconds
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.source = SourceDefinition(
            name=f"GDG - {chapter.name}",
            base_url=f"{SITE_ROOT}/{chapter.slug}/",
            source_type="API",
            connector=f"gdg_api_{chapter.slug.replace('-', '_')}",
            priority=20,
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
        for _ in range(10):
            payload = self._fetch_page(page)
            results = payload.get("results")
            if not isinstance(results, list):
                raise ConnectorError("GDG JSON response has no results list.")
            raw_events.extend(item for item in results if isinstance(item, dict))

            pagination = payload.get("pagination") or {}
            next_page = pagination.get("next_page") if isinstance(pagination, dict) else None
            if not next_page:
                break
            page = int(next_page)
        else:
            raise ConnectorError("GDG pagination exceeded the 10-page safety limit.")

        events = [self._normalize_event(item) for item in raw_events]
        return sorted((event for event in events if event is not None), key=lambda x: x.start_date)

    def _fetch_page(self, page: int) -> dict[str, object]:
        url = f"{API_ROOT}/event_slim/for_chapter/{self.chapter.id}/"
        params = {
            "status": "Live",
            "include_cohosted_events": "true",
            "visible_on_parent_chapter_only": "true",
            "order": "start_date",
            "page_size": 100,
            "page": page,
            "fields": EVENT_FIELDS,
        }
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"GDG API request failed: {exc}") from exc
        if len(response.content) > MAX_RESPONSE_BYTES:
            raise ConnectorError("GDG JSON response exceeded the 5 MB safety limit.")
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/json" not in content_type:
            raise ConnectorError("GDG endpoint returned non-JSON content.")
        try:
            payload = response.json()
        except requests.JSONDecodeError as exc:
            raise ConnectorError(f"GDG returned invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ConnectorError("GDG returned an unexpected JSON structure.")
        return payload

    def _normalize_event(self, raw: dict[str, object]) -> Event | None:
        title = str(raw.get("title") or "").strip()
        source_event_id = str(raw.get("id") or "").strip()
        if not title or not source_event_id or not raw.get("start_date"):
            return None
        if raw.get("is_hidden") is True:
            return None

        try:
            start_utc = self._parse_datetime(str(raw["start_date"]))
            end_utc = (
                self._parse_datetime(str(raw["end_date"]))
                if raw.get("end_date")
                else None
            )
        except ValueError as exc:
            raise ConnectorError(
                f"GDG event {source_event_id} has an invalid date: {exc}"
            ) from exc
        if (end_utc or start_utc) < self.now:
            return None

        timezone_name = str(raw.get("event_timezone") or "America/Lima")
        try:
            event_timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            timezone_name = "America/Lima"
            event_timezone = ZoneInfo(timezone_name)
        start_date = start_utc.astimezone(event_timezone)
        end_date = end_utc.astimezone(event_timezone) if end_utc else None

        tags = [str(tag).strip() for tag in (raw.get("tags") or []) if str(tag).strip()]
        organization = str(raw.get("chapter_title") or self.chapter.name).strip()
        modality = self._modality(raw)
        source_url = self._event_url(raw)
        external_registration = self._safe_url(
            str(raw.get("custom_tickets_url") or raw.get("cohost_registration_url") or "")
        )
        registration_url = external_registration or source_url
        description = self._plain_text(
            str(raw.get("description") or raw.get("description_short") or "")
        )
        venue_parts = [
            str(raw.get(field) or "").strip()
            for field in ("venue_name", "venue_address", "venue_city", "venue_state")
        ]
        venue = ", ".join(dict.fromkeys(part for part in venue_parts if part)) or None
        event_type_title = normalize_text(str(raw.get("event_type_title") or ""))
        is_free = True if "free" in event_type_title or "gratuit" in event_type_title else None
        image_url = self._safe_url(
            str(raw.get("cropped_banner_url") or raw.get("cropped_picture_url") or "")
        )
        event_hash = build_event_hash(
            title, start_date, organization, self.chapter.city
        )

        return Event(
            title=title,
            slug=build_slug(title, start_date, source_event_id),
            description=description,
            organization=organization,
            category="Other",
            tags=tags,
            event_type=infer_event_type(title, tags),
            start_date=start_date,
            end_date=end_date,
            timezone=timezone_name,
            modality=modality,
            venue=venue,
            city=self.chapter.city,
            country=self.chapter.country,
            is_free=is_free,
            registration_url=registration_url,
            source_url=source_url,
            image_url=image_url,
            source="GDG",
            source_event_id=source_event_id,
            event_hash=event_hash,
            status="published",
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _modality(raw: dict[str, object]) -> str:
        audience_type = normalize_text(str(raw.get("audience_type") or ""))
        if "hybrid" in audience_type:
            return "hybrid"
        if raw.get("is_virtual_event") is True or "virtual" in audience_type:
            return "virtual"
        return "in_person"

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

    @staticmethod
    def _event_url(raw: dict[str, object]) -> str:
        relative_url = str(raw.get("relative_url") or "").strip()
        if relative_url.startswith("/events/details/"):
            return SITE_ROOT + relative_url
        static_url = GDGConnector._safe_url(str(raw.get("static_url") or ""))
        return static_url or SITE_ROOT + "/events/"


