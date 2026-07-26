"""Validation helpers for Project Memory metadata."""

from __future__ import annotations

from datetime import date
import re

from metadata_defaults import (
    ALLOWED_AUDIENCES,
    ALLOWED_DOC_TYPES,
    ALLOWED_STATUSES,
    EXPECTED_DOC_TYPES,
    LIST_FIELDS,
    REQUIRED_FIELDS,
)


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_iso_date(value: object) -> bool:
    if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_metadata(
    data: dict[str, object], filename: str | None = None
) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    errors.extend(_validate_choice_fields(data, filename))
    errors.extend(_validate_audience(data))
    errors.extend(_validate_dates(data))
    errors.extend(_validate_list_fields(data))
    return errors


def _validate_choice_fields(
    data: dict[str, object], filename: str | None
) -> list[str]:
    errors: list[str] = []
    if data["doc_type"] not in ALLOWED_DOC_TYPES:
        errors.append(f"Invalid doc_type: {data['doc_type']}")
    elif filename in EXPECTED_DOC_TYPES:
        expected_type = EXPECTED_DOC_TYPES[filename]
        if data["doc_type"] != expected_type:
            errors.append(
                f"Invalid doc_type for {filename}: expected {expected_type}, "
                f"got {data['doc_type']}"
            )
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
        if value is not None and not is_iso_date(value):
            errors.append(f"Invalid date format for {field}: {value}")
    return errors


def _validate_list_fields(data: dict[str, object]) -> list[str]:
    return [
        f"{field} must be a list"
        for field in LIST_FIELDS
        if not isinstance(data.get(field), list)
    ]
