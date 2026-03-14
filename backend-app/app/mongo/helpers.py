"""MongoDB serialization helpers."""

from collections.abc import Mapping
from typing import Any

from bson import ObjectId
from pydantic import HttpUrl


def convert_objectid_to_str(doc: Any) -> Any:
    """Recursively convert ObjectId to str in dict or list."""
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, dict):
        return {k: convert_objectid_to_str(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [convert_objectid_to_str(item) for item in doc]
    return doc


def convert_httpurls_to_strings(doc: Any) -> Any:
    """Recursively convert HttpUrl objects to plain strings."""
    if isinstance(doc, HttpUrl):
        return str(doc)
    if isinstance(doc, Mapping) and not isinstance(doc, type):
        return {k: convert_httpurls_to_strings(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [convert_httpurls_to_strings(item) for item in doc]
    return doc
