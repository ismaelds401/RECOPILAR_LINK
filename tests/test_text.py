from datetime import UTC, datetime

from backend.utils.text import build_event_hash, normalize_text


def test_normalize_text_ignores_case_accents_and_punctuation() -> None:
    assert normalize_text("  Inteligencia ARTIFICIAL — Perú! ") == (
        "inteligencia artificial peru"
    )


def test_event_hash_is_stable_for_equivalent_text() -> None:
    start = datetime(2026, 9, 5, 19, tzinfo=UTC)
    first = build_event_hash("Google Cloud AI", start, "GDG Perú", "Lima")
    second = build_event_hash("GOOGLE CLOUD AI!", start, "gdg peru", "LIMA")
    assert first == second


