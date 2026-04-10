"""Ordered YouTube Data API keys from configuration.

Primary key is required when YouTube features run; optional ``_2`` is used
after the primary key's daily quota is exhausted for the same batch term.
"""

from app.core.config import config


def _collect_keys() -> list[str]:
    keys: list[str] = []
    primary = (config.YOUTUBE_API_KEY_V3 or "").strip()
    if primary:
        keys.append(primary)
    secondary = (config.YOUTUBE_API_KEY_V3_2 or "").strip()
    if secondary:
        keys.append(secondary)
    return keys


def get_ordered_youtube_api_keys() -> list[str]:
    """Return non-empty API key strings in order: primary, then optional second.

    Raises:
        ValueError: If no keys are configured (required for batch workers).
    """
    keys = _collect_keys()
    if not keys:
        msg = "At least YOUTUBE_API_KEY_V3 must be set for YouTube batch processing"
        raise ValueError(msg)
    return keys


def youtube_key_labels_for_ui() -> list[str]:
    """Labels aligned with configured keys (empty if none)."""
    n = len(_collect_keys())
    if n == 0:
        return []
    if n == 1:
        return ["Primary"]
    return ["Primary", "Secondary"][:n]


def configured_youtube_key_count() -> int:
    """Number of API keys in env (0 if none)."""
    return len(_collect_keys())
