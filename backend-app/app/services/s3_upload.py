"""Generic S3 upload helper (EP-05 / SBL-17)."""

from __future__ import annotations

from urllib.parse import quote

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import config


class S3UploadError(Exception):
    """Raised when the object cannot be stored or an accessible URL cannot be produced."""


def _s3_client() -> BaseClient:
    kwargs: dict[str, str] = {"region_name": config.AWS_REGION}
    if config.THUMBNAIL_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.THUMBNAIL_S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def _guess_content_type(key: str) -> str:
    lower = key.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def _direct_url(key: str) -> str:
    bucket = config.THUMBNAIL_S3_BUCKET
    if config.THUMBNAIL_S3_PUBLIC_BASE_URL:
        base = config.THUMBNAIL_S3_PUBLIC_BASE_URL.rstrip("/")
        return f"{base}/{quote(key, safe='/')}"
    if config.THUMBNAIL_S3_ENDPOINT_URL:
        base = config.THUMBNAIL_S3_ENDPOINT_URL.rstrip("/")
        return f"{base}/{bucket}/{quote(key, safe='/')}"
    region = config.AWS_REGION
    host = f"{bucket}.s3.{region}.amazonaws.com"
    return f"https://{host}/{quote(key, safe='/')}"


def _object_read_url(client: BaseClient, key: str) -> str:
    """Return a URL to read an existing object (direct or presigned per config)."""
    if config.THUMBNAIL_S3_USE_PRESIGNED_URL:
        try:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": config.THUMBNAIL_S3_BUCKET, "Key": key},
                ExpiresIn=config.THUMBNAIL_S3_PRESIGNED_EXPIRES_SECONDS,
            )
        except (ClientError, BotoCoreError) as exc:
            raise S3UploadError(
                f"S3 presigned URL generation failed for key {key!r}: {exc}"
            ) from exc
    return _direct_url(key)


def get_s3_object_read_url(key: str) -> str:
    """Return an accessible read URL for an object already in the bucket."""
    if not config.THUMBNAIL_S3_BUCKET:
        raise S3UploadError(
            "S3 bucket is not configured (set THUMBNAIL_S3_BUCKET in the environment)"
        )
    client = _s3_client()
    return _object_read_url(client, key)


def upload_to_s3(data: bytes, key: str) -> str:
    """Upload bytes to S3. Returns an accessible URL (direct or presigned per config)."""
    if not config.THUMBNAIL_S3_BUCKET:
        raise S3UploadError(
            "S3 bucket is not configured (set THUMBNAIL_S3_BUCKET in the environment)"
        )
    client = _s3_client()
    try:
        client.put_object(
            Bucket=config.THUMBNAIL_S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=_guess_content_type(key),
        )
    except (ClientError, BotoCoreError) as exc:
        raise S3UploadError(
            f"S3 put_object failed for key {key!r} in bucket "
            f"{config.THUMBNAIL_S3_BUCKET!r}: {exc}"
        ) from exc

    return _object_read_url(client, key)
