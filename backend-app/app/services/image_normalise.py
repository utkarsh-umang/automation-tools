"""Coerce user-uploaded images into a format the generation models accept.

Both image backends (OpenAI ``images.edit``, Gemini) accept JPEG, PNG and WebP
and nothing else, and both decide by the ``Content-Type`` they are handed rather
than by sniffing the body. Our S3 layer stamps that ``Content-Type`` from the
object key's extension, so an upload we cannot name correctly lands as
``reference.bin`` → ``application/octet-stream`` → a provider 400 raised inside
the Celery worker, minutes after the user pressed Generate, worded in terms of
an API they never called.

That is exactly how AVIF references failed: the file picker allows ``image/*``,
AVIF is a perfectly good ``image/*``, and nothing between the picker and the
provider ever looked at the bytes. So the format question is settled here, at
the edge, from the magic bytes: a directly-supported image passes through
untouched, anything else Pillow can decode is transcoded, and anything else at
all is a 400 the user sees immediately and can act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

# Formats the providers take as-is, mapped to the extension we store them under.
# Pass-through is byte-for-byte: re-encoding a JPEG that was already fine would
# cost a generation of quantisation for nothing.
_PASSTHROUGH_EXT: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
}

# Modes that carry an alpha channel outright. Palette images ("P") carry it only
# when a transparency entry is present, so they are checked separately.
_ALPHA_MODES = frozenset({"RGBA", "LA", "PA"})

_ADVICE = "Re-save it as PNG, JPEG or WebP and upload again."


class UnsupportedImageError(ValueError):
    """The upload is not an image we can decode into a provider-supported format."""


@dataclass(frozen=True)
class NormalisedImage:
    """Bytes to store, and the extension that names their real format.

    ``ext`` is the whole contract with :mod:`app.constants.s3_keys` — it decides
    the object key, which decides the ``Content-Type``, which decides whether the
    provider accepts the image.
    """

    data: bytes
    ext: str


def _describe(filename: str | None, content_type: str | None) -> str:
    named = f"'{filename}'" if filename else "the upload"
    base_ct = (content_type or "").split(";")[0].strip().lower()
    return f"{named} ({base_ct})" if base_ct else named


def normalise_input_image(
    data: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> NormalisedImage:
    """Return provider-ready bytes plus the extension naming their real format.

    ``filename`` and ``content_type`` are advisory: they only ever appear in the
    error message. The format is read from the bytes, which also covers the case
    the browser lies — dragging an image out of a page routinely yields AVIF or
    WebP data under a ``.png`` name.

    :raises UnsupportedImageError: the payload is not a decodable image.
    """
    try:
        with Image.open(BytesIO(data)) as im:
            passthrough_ext = _PASSTHROUGH_EXT.get(im.format or "")
            if passthrough_ext is not None:
                return NormalisedImage(data, passthrough_ext)
            has_alpha = im.mode in _ALPHA_MODES or "transparency" in im.info
            # Multi-frame sources (animated GIF/WebP/AVIF) collapse to their first
            # frame — the providers take a still either way.
            converted = im.convert("RGBA" if has_alpha else "RGB")
    except UnidentifiedImageError as exc:
        raise UnsupportedImageError(
            f"{_describe(filename, content_type)} could not be read as an image. {_ADVICE}"
        ) from exc
    except Image.DecompressionBombError as exc:
        # Pillow's own guard: the pixel count would blow up memory on decode,
        # regardless of how small the compressed upload was.
        raise UnsupportedImageError(
            f"{_describe(filename, content_type)} decodes to too many pixels to process. "
            "Downscale it and upload again."
        ) from exc
    except OSError as exc:  # truncated or otherwise corrupt payload
        raise UnsupportedImageError(
            f"{_describe(filename, content_type)} is a damaged or incomplete image. {_ADVICE}"
        ) from exc

    buf = BytesIO()
    if has_alpha:
        # PNG is the only lossless one of the three, so it is the only honest
        # target for an image whose transparency has to survive.
        converted.save(buf, format="PNG", optimize=True)
        return NormalisedImage(buf.getvalue(), ".png")
    # Everything opaque goes to JPEG: a transcoded 4K frame stays in the hundreds
    # of KB instead of the tens of MB the same frame costs as PNG, and these are
    # reference photos, not line art.
    converted.save(buf, format="JPEG", quality=90, optimize=True)
    return NormalisedImage(buf.getvalue(), ".jpg")
