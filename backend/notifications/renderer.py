"""Safe plain-text and HTML rendering for event digests."""

from __future__ import annotations

from datetime import datetime
from html import escape
from urllib.parse import quote
from zoneinfo import ZoneInfo

from backend.notifications.models import DigestEvent


LIMA = ZoneInfo("America/Lima")
MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)
MODALITY_LABELS = {
    "in_person": "Presencial",
    "virtual": "Virtual",
    "hybrid": "Híbrido",
}


def _event_date(event: DigestEvent) -> str:
    local = event.start_date.astimezone(LIMA)
    return f"{local.day} de {MONTHS[local.month - 1]} · {local:%H:%M}"


def _detail_url(site_url: str, event: DigestEvent) -> str:
    return f"{site_url}/?event={quote(event.slug, safe='')}"


def build_subject(events: list[DigestEvent], *, now: datetime) -> str:
    local = now.astimezone(LIMA)
    noun = "evento nuevo" if len(events) == 1 else "eventos nuevos"
    return f"TechEvents Perú: {len(events)} {noun} · {local.day} {MONTHS[local.month - 1][:3]}"


def render_plain(events: list[DigestEvent], *, site_url: str) -> str:
    lines = [
        f"Encontramos {len(events)} eventos tecnológicos nuevos para ti.",
        "",
    ]
    for index, event in enumerate(events, 1):
        place = " · ".join(
            value
            for value in (MODALITY_LABELS.get(event.modality, event.modality), event.city)
            if value
        )
        lines.extend(
            (
                f"{index}. {event.title}",
                f"   {event.organization or event.source}",
                f"   {_event_date(event)} · {place}",
                f"   {event.category}{' · GRATIS' if event.is_free is True else ''}",
                f"   {_detail_url(site_url, event)}",
                "",
            )
        )
    lines.extend(("Ver todos los eventos:", site_url, "", "TechEvents Perú"))
    return "\n".join(lines)


def render_html(events: list[DigestEvent], *, site_url: str) -> str:
    cards = []
    for event in events:
        place = " · ".join(
            value
            for value in (MODALITY_LABELS.get(event.modality, event.modality), event.city)
            if value
        )
        free_badge = (
            '<span style="background:#d9f99d;color:#123c2e;padding:4px 8px;'
            'border-radius:999px;font-size:11px;font-weight:700">GRATIS</span>'
            if event.is_free is True
            else ""
        )
        cards.append(
            f"""
            <div style="border:1px solid #dfe8e2;border-radius:16px;padding:20px;margin:14px 0;background:#ffffff">
              <div style="font-size:12px;color:#047857;font-weight:700">{escape(event.category)} {free_badge}</div>
              <h2 style="font-size:19px;line-height:1.3;color:#123c2e;margin:10px 0 6px">{escape(event.title)}</h2>
              <div style="font-size:14px;color:#52635d">{escape(event.organization or event.source)}</div>
              <div style="font-size:14px;color:#52635d;margin-top:8px">{escape(_event_date(event))} · {escape(place)}</div>
              <a href="{escape(_detail_url(site_url, event), quote=True)}" style="display:inline-block;margin-top:16px;background:#123c2e;color:#ffffff;text-decoration:none;padding:10px 15px;border-radius:10px;font-weight:700">Ver evento</a>
            </div>
            """
        )
    return f"""<!doctype html>
<html lang="es"><body style="margin:0;background:#f3f6f1;font-family:Arial,sans-serif;color:#123c2e">
  <div style="max-width:640px;margin:0 auto;padding:28px 18px">
    <div style="background:#123c2e;border-radius:20px;padding:26px;color:#ffffff">
      <div style="color:#bef264;font-size:12px;font-weight:700;letter-spacing:1px">TECH EVENTS PERÚ</div>
      <h1 style="font-size:27px;line-height:1.15;margin:10px 0">{len(events)} eventos tecnológicos nuevos</h1>
      <p style="color:#d1e4dc;margin:0">Un resumen breve según tus preferencias.</p>
    </div>
    {''.join(cards)}
    <p style="text-align:center;margin:26px 0"><a href="{escape(site_url, quote=True)}" style="color:#047857;font-weight:700">Explorar todos los eventos</a></p>
    <p style="font-size:11px;line-height:1.5;color:#73817c;text-align:center">Recibes este resumen desde una automatización privada de TechEvents Perú. Confirma siempre los detalles con el organizador.</p>
  </div>
</body></html>"""

