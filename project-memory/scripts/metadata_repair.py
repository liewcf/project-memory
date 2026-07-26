"""Repair helpers for Project Memory metadata."""

from __future__ import annotations

from metadata_defaults import (
    ALLOWED_AUDIENCES,
    ALLOWED_STATUSES,
    LIST_FIELDS,
    expected_metadata,
    today,
)
from metadata_frontmatter import parse_frontmatter, render_frontmatter
from metadata_validation import is_iso_date


def repair_metadata(
    data: dict[str, object],
    filename: str,
    touch: bool = False,
) -> tuple[dict[str, object], bool]:
    defaults = expected_metadata(filename)
    repaired: dict[str, object] = dict(data)
    changed = False
    today_str = today()

    changed = _repair_scalar_fields(repaired, defaults) or changed
    changed = _repair_dates(repaired, today_str, touch, changed) or changed
    changed = _repair_list_fields(repaired, defaults) or changed
    changed = _repair_audience(repaired, defaults) or changed

    if changed and repaired.get("updated") != today_str:
        repaired["updated"] = today_str

    return repaired, changed


def _repair_scalar_fields(
    repaired: dict[str, object],
    defaults: dict[str, object],
) -> bool:
    changed = False
    for field in ("title", "description", "doc_type", "status"):
        if field not in repaired or repaired[field] is None:
            repaired[field] = defaults[field]
            changed = True
        elif field == "doc_type" and repaired[field] != defaults[field]:
            repaired[field] = defaults[field]
            changed = True
        elif field == "status" and repaired[field] not in ALLOWED_STATUSES:
            repaired[field] = defaults[field]
            changed = True
    return changed


def _repair_dates(
    repaired: dict[str, object],
    today_str: str,
    touch: bool,
    changed: bool,
) -> bool:
    date_changed = False
    created_val = repaired.get("created")
    if not is_iso_date(created_val):
        repaired["created"] = today_str
        date_changed = True

    updated_val = repaired.get("updated")
    updated_invalid = not is_iso_date(updated_val)
    if updated_invalid:
        repaired["updated"] = today_str
        date_changed = True
    elif changed or touch:
        if repaired["updated"] != today_str:
            date_changed = True
        repaired["updated"] = today_str
    return date_changed


def _repair_list_fields(
    repaired: dict[str, object],
    defaults: dict[str, object],
) -> bool:
    changed = False
    for field in LIST_FIELDS:
        if not isinstance(repaired.get(field), list):
            repaired[field] = list(defaults[field])
            changed = True
    return changed


def _repair_audience(
    repaired: dict[str, object],
    defaults: dict[str, object],
) -> bool:
    if isinstance(repaired.get("audience"), list):
        invalid = [
            v for v in repaired["audience"] if v not in ALLOWED_AUDIENCES
        ]
        if invalid:
            repaired["audience"] = list(defaults["audience"])
            return True
    return False


def ensure_frontmatter(
    text: str,
    filename: str,
    touch: bool = False,
) -> tuple[str, str]:
    metadata, body, had_fm = parse_frontmatter(text)
    repaired, changed = repair_metadata(metadata, filename, touch=touch)

    if had_fm and not changed:
        return text, "unchanged"

    new_text = f"---\n{render_frontmatter(repaired)}---\n"
    if body:
        if not body.startswith("\n"):
            new_text += "\n"
        new_text += body

    status = "updated" if had_fm else "added"
    return new_text, status
