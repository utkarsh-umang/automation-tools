"""Unit tests for ``mongo_repo`` (mocked collection)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from app.repositories import mongo_repo


@patch("app.repositories.mongo_repo._collection")
def test_create_details_inserts(mock_coll_fn: MagicMock) -> None:
    coll = MagicMock()
    mock_coll_fn.return_value = coll
    mongo_repo.create_details(
        "job-1",
        {
            "reference_image_url": "u",
            "base_image_urls": [],
            "title": "t",
            "include_title": True,
            "creative_comments": "",
            "model": "m",
            "created_at": datetime.now(UTC),
        },
    )
    coll.insert_one.assert_called_once()
    doc = coll.insert_one.call_args[0][0]
    assert doc["job_id"] == "job-1"
    assert doc["title"] == "t"


@patch("app.repositories.mongo_repo._collection")
def test_get_details_many(mock_coll_fn: MagicMock) -> None:
    coll = MagicMock()
    coll.find.return_value = [
        {"job_id": "a", "title": "one"},
        {"job_id": "b", "title": "two"},
    ]
    mock_coll_fn.return_value = coll
    out = mongo_repo.get_details_many(["a", "b"])
    assert out == {
        "a": {"job_id": "a", "title": "one"},
        "b": {"job_id": "b", "title": "two"},
    }
    coll.find.assert_called_once_with({"job_id": {"$in": ["a", "b"]}})


@patch("app.repositories.mongo_repo._collection")
def test_get_details_many_empty_ids(mock_coll_fn: MagicMock) -> None:
    assert mongo_repo.get_details_many([]) == {}
    mock_coll_fn.assert_not_called()


@patch("app.repositories.mongo_repo._collection")
def test_get_details(mock_coll_fn: MagicMock) -> None:
    coll = MagicMock()
    coll.find_one.return_value = {"job_id": "x", "title": "y"}
    mock_coll_fn.return_value = coll
    out = mongo_repo.get_details("x")
    assert out == {"job_id": "x", "title": "y"}
    coll.find_one.assert_called_once_with({"job_id": "x"})


@patch("app.repositories.mongo_repo._collection")
def test_update_prompt_used(mock_coll_fn: MagicMock) -> None:
    coll = MagicMock()
    mock_coll_fn.return_value = coll
    mongo_repo.update_prompt_used("j1", "p1")
    coll.update_one.assert_called_once_with(
        {"job_id": "j1"},
        {"$set": {"prompt_used": "p1"}},
    )


@patch("app.repositories.mongo_repo._collection")
def test_ensure_indexes(mock_coll_fn: MagicMock) -> None:
    coll = MagicMock()
    mock_coll_fn.return_value = coll
    mongo_repo.ensure_thumbnail_job_details_indexes()
    coll.create_index.assert_any_call(
        "job_id",
        unique=True,
        name="idx_thumbnail_job_details_job_id",
    )
    coll.create_index.assert_any_call(
        [("model", 1), ("created_at", 1)],
        name="idx_thumbnail_job_details_model_created_at",
    )
    assert coll.create_index.call_count == 2
