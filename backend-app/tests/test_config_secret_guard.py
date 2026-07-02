"""SECRET_KEY fail-fast guard (P0-2)."""

import pytest

from app.core.config import _INSECURE_SECRET_KEY, Settings


def test_production_with_default_secret_raises() -> None:
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(ENVIRONMENT="production", SECRET_KEY=_INSECURE_SECRET_KEY)


def test_production_with_real_secret_ok() -> None:
    s = Settings(ENVIRONMENT="production", SECRET_KEY="a" * 64)
    assert s.SECRET_KEY == "a" * 64


def test_local_with_default_secret_ok() -> None:
    # Local dev must stay frictionless — the insecure default is allowed.
    s = Settings(ENVIRONMENT="local", SECRET_KEY=_INSECURE_SECRET_KEY)
    assert s.ENVIRONMENT == "local"
