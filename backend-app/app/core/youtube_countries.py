"""Canonical country allowlist for YouTube lead qualification.

The YouTube Data API's ``channels.snippet.country`` field returns ISO 3166-1
alpha-2 codes (e.g. ``"GB"`` for the United Kingdom, ``"AU"`` for Australia,
``"AE"`` for the United Arab Emirates) — not the shorthand names used in
casual business conversation (``"UK"``, ``"AUS"``, ``"UAE"``). ``_ALIASES``
maps those common shorthands onto their canonical ISO code so the allowlist
below can be read the way the business actually talks about it, while every
comparison still happens on the canonical code.

This is a strict allowlist: anything that does not normalize to a code in
``ALLOWED_COUNTRIES`` — including missing, empty, or unrecognized values —
is rejected. See docs/youtube-country-filter-rca.md for why the previous
denylist-based check let channels from unlisted countries through.
"""

from __future__ import annotations

# Canonical ISO 3166-1 alpha-2 codes the business wants leads sourced from.
ALLOWED_COUNTRIES: frozenset[str] = frozenset(
    {
        "US",  # United States
        "GB",  # United Kingdom
        "NZ",  # New Zealand
        "AU",  # Australia
        "AE",  # United Arab Emirates
        "SG",  # Singapore
        "CA",  # Canada
    }
)

# Common non-ISO shorthands seen in specs/UI copy, mapped to their canonical
# ISO 3166-1 alpha-2 code. Extend this map, not ALLOWED_COUNTRIES, if a new
# shorthand needs to be accepted as input.
_ALIASES: dict[str, str] = {
    "UK": "GB",
    "AUS": "AU",
    "UAE": "AE",
}


def normalize_country_code(raw: str | None) -> str | None:
    """Normalize a raw country value to a canonical ISO 3166-1 alpha-2 code.

    Trims whitespace, upper-cases, and resolves known aliases (UK->GB,
    AUS->AU, UAE->AE). Returns ``None`` for missing, empty, or blank input —
    callers must treat ``None`` as "unknown," never as a wildcard pass.
    """
    if not raw:
        return None
    code = raw.strip().upper()
    if not code:
        return None
    return _ALIASES.get(code, code)


def is_allowed_country(raw: str | None) -> bool:
    """True only if ``raw`` normalizes to a code in ``ALLOWED_COUNTRIES``.

    Strict allowlist semantics: missing, empty, malformed, or unrecognized
    values all return False. There is no permissive fallback.
    """
    code = normalize_country_code(raw)
    return code is not None and code in ALLOWED_COUNTRIES
