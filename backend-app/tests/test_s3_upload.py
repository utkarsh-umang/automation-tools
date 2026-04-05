"""Unit tests for ``upload_to_s3`` (mocked boto3 client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.config import config
from app.services.s3_upload import S3UploadError, upload_to_s3


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@patch("app.services.s3_upload._s3_client")
def test_upload_to_s3_direct_url(mock_factory: MagicMock, mock_client: MagicMock) -> None:
    mock_factory.return_value = mock_client
    mock_client.generate_presigned_url = MagicMock()
    with patch.object(config, "THUMBNAIL_S3_BUCKET", "my-bucket"):
        with patch.object(config, "AWS_REGION", "us-east-1"):
            with patch.object(config, "THUMBNAIL_S3_ENDPOINT_URL", None):
                with patch.object(config, "THUMBNAIL_S3_PUBLIC_BASE_URL", None):
                    with patch.object(config, "THUMBNAIL_S3_USE_PRESIGNED_URL", False):
                        url = upload_to_s3(b"\x00", "thumbnails/x.png")
    mock_client.put_object.assert_called_once()
    call_kw = mock_client.put_object.call_args[1]
    assert call_kw["Bucket"] == "my-bucket"
    assert call_kw["Key"] == "thumbnails/x.png"
    assert call_kw["Body"] == b"\x00"
    assert call_kw["ContentType"] == "image/png"
    assert url.startswith("https://my-bucket.s3.us-east-1.amazonaws.com/")
    mock_client.generate_presigned_url.assert_not_called()


@patch("app.services.s3_upload._s3_client")
def test_upload_to_s3_presigned_url(mock_factory: MagicMock, mock_client: MagicMock) -> None:
    mock_factory.return_value = mock_client
    mock_client.generate_presigned_url.return_value = "https://signed.example/get"
    with patch.object(config, "THUMBNAIL_S3_BUCKET", "b"):
        with patch.object(config, "THUMBNAIL_S3_USE_PRESIGNED_URL", True):
            with patch.object(config, "THUMBNAIL_S3_PRESIGNED_EXPIRES_SECONDS", 7200):
                url = upload_to_s3(b"data", "k.png")
    mock_client.put_object.assert_called_once()
    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "b", "Key": "k.png"},
        ExpiresIn=7200,
    )
    assert url == "https://signed.example/get"


@patch("app.services.s3_upload._s3_client")
def test_upload_to_s3_put_failure(mock_factory: MagicMock, mock_client: MagicMock) -> None:
    mock_factory.return_value = mock_client
    mock_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "no"}},
        "PutObject",
    )
    with patch.object(config, "THUMBNAIL_S3_BUCKET", "b"):
        with pytest.raises(S3UploadError) as ei:
            upload_to_s3(b"x", "y.png")
    assert "put_object failed" in str(ei.value).lower()
    assert "y.png" in str(ei.value)


def test_upload_to_s3_missing_bucket() -> None:
    with patch.object(config, "THUMBNAIL_S3_BUCKET", ""):
        with pytest.raises(S3UploadError, match="bucket is not configured"):
            upload_to_s3(b"x", "y.png")


@patch("app.services.s3_upload._s3_client")
def test_upload_presigned_failure(mock_factory: MagicMock, mock_client: MagicMock) -> None:
    mock_factory.return_value = mock_client
    mock_client.generate_presigned_url.side_effect = ClientError(
        {"Error": {"Code": "X", "Message": "bad"}},
        "GetObject",
    )
    with patch.object(config, "THUMBNAIL_S3_BUCKET", "b"):
        with patch.object(config, "THUMBNAIL_S3_USE_PRESIGNED_URL", True):
            with pytest.raises(S3UploadError, match="presigned URL generation failed"):
                upload_to_s3(b"d", "k.png")


def test_thumbnail_s3_key_constant() -> None:
    from app.constants.s3_keys import THUMBNAIL_S3_KEY_PREFIX, thumbnail_s3_key

    jid = "550e8400-e29b-41d4-a716-446655440000"
    assert THUMBNAIL_S3_KEY_PREFIX == "thumbnails"
    assert thumbnail_s3_key(jid) == f"thumbnails/{jid}.png"


@patch("app.services.thumbnail_s3.upload_to_s3")
def test_upload_thumbnail_png_uses_deterministic_key(mock_upload: MagicMock) -> None:
    from app.services.thumbnail_s3 import upload_thumbnail_png

    mock_upload.return_value = "https://x"
    jid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    out = upload_thumbnail_png(jid, b"png")
    assert out == "https://x"
    mock_upload.assert_called_once_with(b"png", f"thumbnails/{jid}.png")
