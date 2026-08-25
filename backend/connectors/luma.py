"""Luma connector based on its official public iCal subscription feed."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import requests
from icalendar import Calendar
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.connectors.base_connector import (
    BaseConnector,
    ConnectorError,
    SourceDefinition,
)
from backend.models.event import Event
from backend.utils.text import (
    build_event_hash,
    build_slug,
    infer_event_type,
    normalize_text,
)

LIMA_TIMEZONE = ZoneInfo("America/Lima")
MAX_FEED_BYTES = 5 * 1024 * 1024
LUMA_URL_PATTERN = re.compile(r"https://(?:lu\.ma|luma\.com)/[\w-]+", re.I)
CALENDAR_ID_PATTERN = re.compile(r"^cal-[A-Za-z0-9]+$")

PERU_CITY_ALIASES = {
    "lima": "Lima",
    "miraflores": "Lima",
    "san isidro": "Lima",
    "magdalena del mar": "Lima",
    "santiago de surco": "Lima",
    "la molina": "Lima",
    "barranco": "Lima",
    "arequipa": "Arequipa",
    "yanahuara": "Arequipa",
    "trujillo": "Trujillo",
    "cusco": "Cusco",
    "piura": "Piura",
    "chiclayo": "Chiclayo",
}

FOREIGN_COUNTRIES = {
    "argentina": "Argentina",
    "bolivia": "Bolivia",
    "bogota": "Colombia",
    "barranquilla": "Colombia",
    "brazil": "Brazil",
    "brasil": "Brazil",
    "chile": "Chile",
    "colombia": "Colombia",
    "ciudad de guatemala": "Guatemala",
    "ecuador": "Ecuador",
    "el salvador": "El Salvador",
    "guatemala": "Guatemala",
    "mexico": "Mexico",
    "san salvador": "El Salvador",
    "uruguay": "Uruguay",
}


class LumaConnector(BaseConnector):
    """Collect published Luma events without using its paid management API."""

    def __init__(
        self,
        calendar_id: str,
        calendar_slug: str,
        calendar_name: str,
        *,
        timeout_seconds: int = 20,
        now: datetime | None = None,
    ) -> None:
        if not CALENDAR_ID_PATTERN.fullmatch(calendar_id):
            raise ValueError("Invalid Luma calendar ID.")
        if not re.fullmatch(r"[A-Za-z0-9-]+", calendar_slug):
            raise ValueError("Invalid Luma calendar slug.")

        self.calendar_id = calendar_id
        self.timeout_seconds = timeout_seconds
        self.now = (now or datetime.now(UTC)).astimezone(UTC)
        self.feed_url = (
            "https://api.luma.com/ics/get?entity=calendar&id=" + calendar_id
        )
        self.source = SourceDefinition(
            name=f"Luma - {calendar_name}",
            base_url=f"https://luma.com/{calendar_slug}",
            source_type="ICAL",
            connector=f"luma_ical_{calendar_slug}",
            priority=10,
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
                "Accept": "text/calendar, text/plain;q=0.9",
            }
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def collect(self) -> list[Event]:
        try:
            response = self.session.get(
                self.feed_url,
                timeout=self.timeout_seconds,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"Luma iCal request failed: {exc}") from exc

        content = response.content
        if len(content) > MAX_FEED_BYTES:
            raise ConnectorError("Luma iCal feed exceeded the 5 MB safety limit.")
        if not content.lstrip().startswith(b"BEGIN:VCALENDAR"):
            raise ConnectorError("Luma returned content that is not an iCal calendar.")

        return self.parse(content)

    def parse(self, content: bytes) -> list[Event]:
        try:
            calendar = Calendar.from_ical(content)
        except Exception as exc:
            raise ConnectorError(f"Invalid Luma iCal content: {exc}") from exc

        events: list[Event] = []
        for component in calendar.walk("VEVENT"):
            event = self._normalize_component(component)
            if event is not None:
                events.append(event)
        return sorted(events, key=lambda item: item.start_date)

    def _normalize_component(self, component: object) -> Event | None:
        title = str(component.get("SUMMARY", "")).strip()
        uid = str(component.get("UID", "")).strip()
        if not title or not uid or component.get("DTSTART") is None:
            return None

        source_event_id = uid.split("@", 1)[0]
        start_date = self._to_lima_datetime(component.decoded("DTSTART"))
        end_value = component.decoded("DTEND") if component.get("DTEND") else None
        end_date = self._to_lima_datetime(end_value) if end_value else None
        comparison_end = end_date or start_date
        if comparison_end.astimezone(UTC) < self.now:
            return None

        description = str(component.get("DESCRIPTION", "")).strip()
        location = str(component.get("LOCATION", "")).strip()
        latitude, longitude = self._extract_geo(component)
        address = self._extract_address(description)
        venue = location if location and not location.startswith("http") else address
        organization = self._extract_organization(component)
        city, country = self._infer_geography(title, venue or description)
        modality = self._infer_modality(title, location, address, latitude)

        # The project initially targets Peru plus internationally available
        # virtual events. Unknown/foreign physical events are excluded.
        if modality != "virtual" and country != "Peru":
            return None

        registration_url = self._extract_registration_url(description)
        source_url = registration_url or self.source.base_url
        event_hash = build_event_hash(title, start_date, organization, city)
        status = (
            "cancelled"
            if str(component.get("STATUS", "")).upper() == "CANCELLED"
            else "published"
        )

        return Event(
            title=title,
            slug=build_slug(title, start_date, source_event_id),
            description=self._clean_description(description),
            organization=organization,
            category="Other",
            tags=[],
            event_type=infer_event_type(title),
            start_date=start_date,
            end_date=end_date,
            timezone="America/Lima",
            modality=modality,
            venue=venue,
            city=city,
            country=country,
            latitude=latitude,
            longitude=longitude,
            is_free=None,
            registration_url=registration_url,
            source_url=source_url,
            source="Luma",
            source_event_id=source_event_id,
            event_hash=event_hash,
            status=status,
        )

    @staticmethod
    def _to_lima_datetime(value: date | datetime) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=LIMA_TIMEZONE)
            return value.astimezone(LIMA_TIMEZONE)
        return datetime.combine(value, time.min, tzinfo=LIMA_TIMEZONE)

    @staticmethod
    def _extract_registration_url(description: str) -> str | None:
        match = LUMA_URL_PATTERN.search(description)
        return match.group(0) if match else None

    @staticmethod
    def _extract_organization(component: object) -> str | None:
        organizer = component.get("ORGANIZER")
        if organizer is None:
            return None
        common_name = organizer.params.get("CN")
        return str(common_name).strip() if common_name else None

    @staticmethod
    def _extract_address(description: str) -> str | None:
        match = re.search(r"Address:\s*(.+?)(?:\n\s*\n|Hosted by)", description, re.S | re.I)
        if not match:
            return None
        address = " ".join(match.group(1).split())
        if normalize_text(address) == "check event page for more details":
            return None
        return address

    @staticmethod
    def _extract_geo(component: object) -> tuple[float | None, float | None]:
        geo = component.get("GEO")
        if geo is None:
            return None, None
        try:
            raw = geo.to_ical()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            else:
                raw = str(raw)
            latitude, longitude = raw.split(";", 1)
            return float(latitude), float(longitude)
        except (AttributeError, TypeError, ValueError):
            return None, None

    @staticmethod
    def _infer_geography(title: str, location_text: str) -> tuple[str | None, str | None]:
        normalized = normalize_text(f"{title} {location_text}")
        city = next(
            (value for alias, value in PERU_CITY_ALIASES.items() if alias in normalized),
            None,
        )
        if "peru" in normalized or city is not None:
            return city, "Peru"
        for alias, country in FOREIGN_COUNTRIES.items():
            if alias in normalized:
                return None, country
        return None, None

    @staticmethod
    def _infer_modality(
        title: str,
        location: str,
        address: str | None,
        latitude: float | None,
    ) -> str:
        normalized = normalize_text(f"{title} {location} {address or ''}")
        if any(word in normalized for word in ("hybrid", "hibrido", "hibrida")):
            return "hybrid"
        if any(word in normalized for word in ("zoom", "google meet", "online", "virtual")):
            return "virtual"
        if latitude is not None or address or (location and not location.startswith("http")):
            return "in_person"
        # Some physical formats intentionally hide their exact address until
        # registration. Their title is the only signal retained in the feed.
        if any(keyword in normalized for keyword in ("full day hackathon", "hacker house")):
            return "in_person"
        if location.startswith("http"):
            return "virtual"
        return "in_person"

    @staticmethod
    def _clean_description(description: str) -> str | None:
        cleaned = re.sub(
            r"Get up-to-date information at:\s*https://\S+",
            "",
            description,
            flags=re.I,
        )
        cleaned = re.sub(r"\n*Hosted by .+$", "", cleaned, flags=re.I | re.S)
        cleaned = "\n".join(line.rstrip() for line in cleaned.strip().splitlines())
        return cleaned or None

