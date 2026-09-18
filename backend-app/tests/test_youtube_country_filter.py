"""Tests for the YouTube lead country allowlist.

Covers app/core/youtube_countries.py (normalization + allowlist membership)
and its integration into app/worker/youtube/evaluate.py::evaluate_channel.

Regression coverage for docs/youtube-country-filter-rca.md: the previous
implementation used a denylist (``excludeCountries``, default ``["IN"]``),
so a channel from any unlisted country -- or with no country set at all --
was admitted. These tests pin the corrected allowlist behaviour so that
regression cannot reappear silently.
"""

import pytest

from app.core.youtube_countries import (
    ALLOWED_COUNTRIES,
    is_allowed_country,
    normalize_country_code,
)
from app.worker.youtube.evaluate import evaluate_channel

# ── app/core/youtube_countries.py ──────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("US", "US"),
        ("GB", "GB"),
        ("gb", "GB"),
        (" gb ", "GB"),
        ("UK", "GB"),
        ("uk", "GB"),
        ("NZ", "NZ"),
        ("AU", "AU"),
        ("AUS", "AU"),
        ("aus", "AU"),
        ("AE", "AE"),
        ("UAE", "AE"),
        ("uae", "AE"),
        ("SG", "SG"),
        ("CA", "CA"),
        ("DE", "DE"),  # unrecognized alias still normalizes; allowlist rejects separately
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_normalize_country_code(raw: str | None, expected: str | None) -> None:
    assert normalize_country_code(raw) == expected


@pytest.mark.parametrize("raw", ["US", "GB", "UK", "NZ", "AU", "AUS", "AE", "UAE", "SG", "CA"])
def test_is_allowed_country_accepts_target_countries(raw: str) -> None:
    assert is_allowed_country(raw) is True


@pytest.mark.parametrize("raw", ["  us  ", "Gb", "aUs", "sg "])
def test_is_allowed_country_normalizes_case_and_whitespace(raw: str) -> None:
    assert is_allowed_country(raw) is True


@pytest.mark.parametrize("raw", ["IN", "DE", "BR", "PH", "NG", "FR", "XX"])
def test_is_allowed_country_rejects_unsupported(raw: str) -> None:
    assert is_allowed_country(raw) is False


def test_is_allowed_country_rejects_missing() -> None:
    assert is_allowed_country(None) is False


def test_is_allowed_country_rejects_empty_string() -> None:
    assert is_allowed_country("") is False


def test_is_allowed_country_rejects_whitespace_only() -> None:
    assert is_allowed_country("   ") is False


def test_allowed_countries_are_canonical_iso_codes() -> None:
    """Guards against accidentally seeding ALLOWED_COUNTRIES with shorthand codes."""
    assert ALLOWED_COUNTRIES == {"US", "GB", "NZ", "AU", "AE", "SG", "CA"}


# ── evaluate_channel integration ───────────────────────────────────────────


def _make_channel(*, country: object = "US", subs: int = 5_000, video_count: int = 40) -> dict:
    snippet: dict = {"title": "Test Channel", "description": "hello@example.com"}
    if country is not _MISSING:
        snippet["country"] = country
    return {
        "id": "UC_test123",
        "snippet": snippet,
        "statistics": {"subscriberCount": str(subs), "videoCount": str(video_count)},
        "contentDetails": {"relatedPlaylists": {"uploads": "UU_test123"}},
    }


_MISSING = object()


def _stub_recent_videos(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the two network calls evaluate_channel makes after the country gate."""
    import datetime

    monkeypatch.setattr(
        "app.worker.youtube.evaluate.get_recent_videos",
        lambda *_a, **_k: [
            {
                "snippet": {
                    "publishedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "resourceId": {"videoId": "vid1"},
                }
            }
        ],
    )
    monkeypatch.setattr(
        "app.worker.youtube.evaluate.get_video_stats",
        lambda *_a, **_k: [{"statistics": {"viewCount": "1000"}}],
    )


def test_evaluate_channel_rejects_missing_country(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: a channel with no `snippet.country` key must not pass silently."""
    channel = _make_channel(country=_MISSING)
    assert evaluate_channel(channel, {}, quota=None) is None


def test_evaluate_channel_rejects_null_country(monkeypatch: pytest.MonkeyPatch) -> None:
    channel = _make_channel(country=None)
    assert evaluate_channel(channel, {}, quota=None) is None


def test_evaluate_channel_rejects_empty_string_country(monkeypatch: pytest.MonkeyPatch) -> None:
    channel = _make_channel(country="")
    assert evaluate_channel(channel, {}, quota=None) is None


def test_evaluate_channel_rejects_unsupported_country(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: this is the exact bug reported -- e.g. a German channel ("DE") used to
    pass because the old check only excluded ``["IN"]``."""
    channel = _make_channel(country="DE")
    assert evaluate_channel(channel, {}, quota=None) is None


def test_evaluate_channel_rejects_before_any_api_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """The country gate must short-circuit before get_recent_videos/get_video_stats run,
    so a disallowed channel never spends quota."""
    calls: list[str] = []
    monkeypatch.setattr(
        "app.worker.youtube.evaluate.get_recent_videos",
        lambda *_a, **_k: calls.append("get_recent_videos") or [],
    )
    monkeypatch.setattr(
        "app.worker.youtube.evaluate.get_video_stats",
        lambda *_a, **_k: calls.append("get_video_stats") or [],
    )
    channel = _make_channel(country="DE")
    assert evaluate_channel(channel, {}, quota=None) is None
    assert calls == []


@pytest.mark.parametrize("raw", ["US", "GB", "UK", "NZ", "AU", "AUS", "AE", "UAE", "SG", "CA"])
def test_evaluate_channel_accepts_target_countries(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    _stub_recent_videos(monkeypatch)
    channel = _make_channel(country=raw)
    lead = evaluate_channel(channel, {}, quota=None)
    assert lead is not None
    assert lead["country"] == normalize_country_code(raw)


def test_evaluate_channel_stores_canonical_code_not_raw_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A channel tagged with the business shorthand ("UK") must be persisted under the
    canonical ISO code ("GB"), never the raw alias."""
    _stub_recent_videos(monkeypatch)
    channel = _make_channel(country="UK")
    lead = evaluate_channel(channel, {}, quota=None)
    assert lead is not None
    assert lead["country"] == "GB"


def test_evaluate_channel_excludeCountries_still_applies_within_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Existing per-batch excludeCountries behaviour is preserved as an additional
    narrowing filter on top of the new hard allowlist."""
    _stub_recent_videos(monkeypatch)
    channel = _make_channel(country="CA")
    lead = evaluate_channel(channel, {"excludeCountries": ["CA"]}, quota=None)
    assert lead is None


def test_evaluate_channel_excludeCountries_normalizes_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A batch configured with the shorthand ("UAE") must still exclude the channel
    whose API-reported country is the canonical code ("AE")."""
    _stub_recent_videos(monkeypatch)
    channel = _make_channel(country="AE")
    lead = evaluate_channel(channel, {"excludeCountries": ["UAE"]}, quota=None)
    assert lead is None
