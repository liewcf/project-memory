"""Validation helpers for Project Memory metadata."""

from __future__ import annotations

import re

from metadata_defaults import (
    ALLOWED_AUDIENCES,
    ALLOWED_DOC_TYPES,
    ALLOWED_STATUSES,
    LIST_FIELDS,
    REQUIRED_FIELDS,
)


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_metadata(
    data: dict[str, object], filename: str | None = None
) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    errors.extend(_validate_choice_fields(data))
    errors.extend(_validate_audience(data))
    errors.extend(_validate_dates(data))
    errors.extend(_validate_list_fields(data))
    return errors


def _validate_choice_fields(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if data["doc_type"] not in ALLOWED_DOC_TYPES:
        errors.append(f"Invalid doc_type: {data['doc_type']}")
    if data["status"] not in ALLOWED_STATUSES:
        errors.append(f"Invalid status: {data['status']}")
    return errors


def _validate_audience(data: dict[str, object]) -> list[str]:
    audience = data["audience"]
    if not isinstance(audience, list):
        return []
    return [
        f"Invalid audience value: {value}"
        for value in audience
        if value not in ALLOWED_AUDIENCES
    ]


def _validate_dates(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for field in ("created", "updated"):
        value = data.get(field)
        if value is not None and not DATE_RE.match(str(value)):
            errors.append(f"Invalid date format for {field}: {value}")
    return errors


def _validate_list_fields(data: dict[str, object]) -> list[str]:
    return [
        f"{field} must be a list"
        for field in LIST_FIELDS
        if not isinstance(data.get(field), list)
    ]
