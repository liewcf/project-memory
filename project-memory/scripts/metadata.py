"""Compatibility imports for Project Memory Metadata v1 helpers."""

from __future__ import annotations

from metadata_defaults import (
    ALLOWED_AUDIENCES,
    ALLOWED_DOC_TYPES,
    ALLOWED_STATUSES,
    DOCS_DIR,
    EXPECTED_DOC_TYPES,
    LIST_FIELDS,
    MEMORY_FILES,
    MINIMAL_BODIES,
    REQUIRED_FIELDS,
    default_body,
    expected_metadata,
    resolve_root,
)
from metadata_frontmatter import parse_frontmatter, render_frontmatter
from metadata_repair import ensure_frontmatter, repair_metadata
from metadata_validation import DATE_RE as _DATE_RE
from metadata_validation import is_iso_date, validate_metadata


__all__ = [
    "ALLOWED_AUDIENCES",
    "ALLOWED_DOC_TYPES",
    "ALLOWED_STATUSES",
    "DOCS_DIR",
    "EXPECTED_DOC_TYPES",
    "LIST_FIELDS",
    "MEMORY_FILES",
    "MINIMAL_BODIES",
    "REQUIRED_FIELDS",
    "_DATE_RE",
    "default_body",
    "ensure_frontmatter",
    "expected_metadata",
    "is_iso_date",
    "parse_frontmatter",
    "render_frontmatter",
    "repair_metadata",
    "resolve_root",
    "validate_metadata",
]
