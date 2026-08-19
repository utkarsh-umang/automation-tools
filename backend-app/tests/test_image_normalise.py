"""Upload normalisation — the guard against provider ``octet-stream`` 400s.

The bug these cover: an AVIF reference sailed through the ``image/*`` file
picker, could not be named by extension, was stored as ``reference.bin`` with
``Content-Type: application/octet-stream``, and was rejected by both OpenAI and
Gemini inside the Celery worker minutes later.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from app.services.image_normalise import (
    UnsupportedImageError,
    normalise_input_image,
)


def _encode(fmt: str, *, mode: str = "RGB", size: tuple[int, int] = (8, 8)) -> bytes:
    buf = BytesIO()
    Image.new(mode, size, "red").save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("fmt", "ext"),
    [("PNG", ".png"), ("JPEG", ".jpg"), ("WEBP", ".webp")],
)
def test_supported_formats_pass_through_unchanged(fmt: str, ext: str) -> None:
    """No re-encode for formats the providers already accept."""
    data = _encode(fmt)
    out = normalise_input_image(data, f"x{ext}", f"image/{fmt.lower()}")
    assert out.ext == ext
    assert out.data is data


def test_avif_is_transcoded_to_jpeg() -> None:
    """The exact failure from production: AVIF in, provider-readable JPEG out."""
    pytest.importorskip("PIL.AvifImagePlugin")
    data = _encode("AVIF")
    out = normalise_input_image(data, "reference.avif", "image/avif")
    assert out.ext == ".jpg"
    assert Image.open(BytesIO(out.data)).format == "JPEG"


def test_gif_is_transcoded_rather_than_stored_as_gif() -> None:
    """GIF was the latent twin of the AVIF bug.

    It was an accepted key extension but had no Content-Type entry, so it would
    have been stored unreadable. It is not a provider-supported format either,
    so the fix is to transcode it, not to add ``.gif`` to the table.
    """
    out = normalise_input_image(_encode("GIF", mode="P"), "loop.gif", "image/gif")
    assert out.ext in (".png", ".jpg")
    assert Image.open(BytesIO(out.data)).format in ("PNG", "JPEG")


def test_transparency_survives_as_png() -> None:
    out = normalise_input_image(_encode("TIFF", mode="RGBA"), "cutout.tiff", "image/tiff")
    assert out.ext == ".png"
    assert Image.open(BytesIO(out.data)).mode == "RGBA"


def test_opaque_transcode_prefers_jpeg() -> None:
    out = normalise_input_image(_encode("TIFF"), "flat.tiff", "image/tiff")
    assert out.ext == ".jpg"


def test_format_is_read_from_bytes_not_from_the_filename() -> None:
    """Browsers routinely hand us WebP/AVIF data under a ``.png`` name."""
    out = normalise_input_image(_encode("WEBP"), "screenshot.png", "image/png")
    assert out.ext == ".webp"


def test_undecodable_payload_raises() -> None:
    with pytest.raises(UnsupportedImageError, match="could not be read as an image"):
        normalise_input_image(b"not an image at all", "notes.txt", "image/png")


def test_truncated_image_raises() -> None:
    truncated = _encode("PNG", size=(64, 64))[:40]
    with pytest.raises(UnsupportedImageError):
        normalise_input_image(truncated, "half.png", "image/png")


def test_error_names_the_file_and_its_claimed_type() -> None:
    with pytest.raises(UnsupportedImageError) as exc:
        normalise_input_image(b"\x00\x01\x02", "broken.avif", "image/avif; charset=binary")
    message = str(exc.value)
    assert "'broken.avif'" in message
    assert "image/avif" in message
