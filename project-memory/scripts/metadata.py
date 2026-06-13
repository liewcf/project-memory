#!/usr/bin/env python3
"""Shared helpers for Project Memory Metadata v1.

Provides constants, frontmatter parsing/rendering, validation, and repair
for the four docs/ memory files.  AGENTS.md is always excluded.

This module uses only the Python standard library.
"""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOCS_DIR = Path("docs")

MEMORY_FILES: tuple[str, ...] = (
    "PROJECT_CONTEXT.md",
    "DECISIONS.md",
    "TASKS.md",
    "CHANGELOG_WORK.md",
)

REQUIRED_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "doc_type",
    "status",
    "created",
    "updated",
    "tags",
    "audience",
    "related",
)

ALLOWED_DOC_TYPES: tuple[str, ...] = (
    "context",
    "decision_log",
    "task_state",
    "work_log",
)

ALLOWED_STATUSES: tuple[str, ...] = (
    "active",
    "stable",
    "archived",
    "draft",
)

ALLOWED_AUDIENCES: tuple[str, ...] = (
    "agent",
    "maintainer",
    "developer",
)

LIST_FIELDS: tuple[str, ...] = ("tags", "audience", "related")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Default metadata templates (one per docs/ memory file)
# ---------------------------------------------------------------------------

def _today() -> str:
    return date.today().isoformat()


def expected_metadata(filename: str) -> dict[str, object]:
    """Return a fresh default metadata dict for *filename*."""
    current_date = _today()
    templates: dict[str, dict[str, object]] = {
        "PROJECT_CONTEXT.md": {
            "title": "Project Context",
            "description": (
                "Stable project facts, structure, workflows, resources, "
                "and constraints."
            ),
            "doc_type": "context",
            "status": "stable",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "context", "durable-knowledge"],
            "audience": ["agent", "maintainer"],
            "related": ["DECISIONS.md", "TASKS.md", "CHANGELOG_WORK.md"],
        },
        "DECISIONS.md": {
            "title": "Decisions",
            "description": (
                "Important project, product, technical, process, or content "
                "decisions with rationale and consequences."
            ),
            "doc_type": "decision_log",
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "decisions", "rationale"],
            "audience": ["agent", "maintainer"],
            "related": [
                "PROJECT_CONTEXT.md",
                "TASKS.md",
                "CHANGELOG_WORK.md",
            ],
        },
        "TASKS.md": {
            "title": "Current Tasks",
            "description": (
                "Current tasks, blockers, verification state, and "
                "recommended next actions."
            ),
            "doc_type": "task_state",
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "tasks", "current-state"],
            "audience": ["agent", "maintainer"],
            "related": [
                "PROJECT_CONTEXT.md",
                "DECISIONS.md",
                "CHANGELOG_WORK.md",
            ],
        },
        "CHANGELOG_WORK.md": {
            "title": "Work Changelog",
            "description": (
                "Dated notes on changed files, deliverables, tooling, "
                "checks, and verification."
            ),
            "doc_type": "work_log",
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": [
                "project-memory",
                "changelog",
                "work-log",
                "verification",
            ],
            "audience": ["agent", "maintainer"],
            "related": [
                "PROJECT_CONTEXT.md",
                "DECISIONS.md",
                "TASKS.md",
            ],
        },
    }
    return dict(templates[filename])


# ---------------------------------------------------------------------------
# Minimal body content (used by repair when a docs file is missing entirely)
# ---------------------------------------------------------------------------

MINIMAL_BODIES: dict[str, str] = {
    "PROJECT_CONTEXT.md": (
        "# Project Context\n\nNo durable context recorded yet.\n"
    ),
    "DECISIONS.md": "# Decisions\n\nNo decisions recorded yet.\n",
    "TASKS.md": "# Current Tasks\n\nNo current tasks recorded yet.\n",
    "CHANGELOG_WORK.md": (
        "# Work Changelog\n\nNo work log entries recorded yet.\n"
    ),
}


def default_body(filename: str) -> str:
    """Return the minimal body used when creating a missing docs file."""
    return MINIMAL_BODIES[filename]


# ---------------------------------------------------------------------------
# Root resolution
# ---------------------------------------------------------------------------

def resolve_root(root_arg: str | None = None) -> Path:
    """Return *root_arg* as a Path, or the current working directory."""
    if root_arg is not None:
        return Path(root_arg)
    return Path(os.getcwd())


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(
    text: str,
) -> tuple[dict[str, object], str, bool]:
    """Parse YAML frontmatter from Markdown *text*.

    Returns ``(metadata_dict, body_str, had_frontmatter)``.

    Supports the Project Memory Metadata v1 subset:
    ``---`` delimiters, scalar strings, quoted strings, block lists.
    Raises ``ValueError`` on unsupported YAML constructs.
    """
    stripped = text.lstrip("\n")
    if not stripped.startswith("---"):
        return {}, text, False

    # Find the closing ---
    rest = stripped[3:]
    if rest.startswith("\n"):
        rest = rest[1:]

    # Locate closing delimiter at the start of a line
    close_pattern = re.compile(r"^---[ \t]*$", re.MULTILINE)
    match = close_pattern.search(rest)
    if match is None:
        return {}, text, False

    yaml_block = rest[: match.start()]
    body = rest[match.end() :]
    if body.startswith("\n"):
        body = body[1:]

    metadata = _parse_yaml_block(yaml_block)
    return metadata, body, True


def _parse_yaml_block(block: str) -> dict[str, object]:
    """Parse a simple YAML block into a dict (Metadata v1 subset only)."""
    result: dict[str, object] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for raw_line in block.split("\n"):
        # Blank line
        if raw_line.strip() == "":
            continue

        # Comment line
        if raw_line.lstrip().startswith("#"):
            continue

        # Block list item (starts with whitespace + "- ")
        list_match = re.match(r"^[ \t]+- (.+)$", raw_line)
        if list_match and current_key is not None:
            value = list_match.group(1).strip()
            value = _strip_quotes(value)
            if current_list is None:
                current_list = []
            current_list.append(value)
            result[current_key] = current_list
            continue

        # Key: value pair
        kv_match = re.match(r"^(\w[\w-]*)[ \t]*:[ \t]*(.*)$", raw_line)
        if kv_match:
            # Flush any previous list
            current_key = kv_match.group(1)
            raw_value = kv_match.group(2).strip()

            # Reject unsupported constructs
            if raw_value.startswith("{") or raw_value.startswith("["):
                raise ValueError(
                    f"Unsupported YAML syntax for key '{current_key}': "
                    f"flow mappings/sequences are not supported"
                )

            current_list = None  # reset list accumulator

            if raw_value == "":
                # Next indented lines may be a block list
                result[current_key] = None
            else:
                result[current_key] = _strip_quotes(raw_value)
            continue

        # Indented but not a list item — likely nested mapping
        if raw_line.startswith(("  ", "\t")) and current_key is not None:
            raise ValueError(
                f"Unsupported nested YAML under key '{current_key}'"
            )

    return result


def _strip_quotes(value: str) -> str:
    """Remove matching surrounding quotes from a string value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or (
            value[0] == "'" and value[-1] == "'"
        ):
            return value[1:-1]
    return value


# ---------------------------------------------------------------------------
# Frontmatter renderer
# ---------------------------------------------------------------------------

def render_frontmatter(data: dict[str, object]) -> str:
    """Render *data* as a YAML frontmatter string (without ``---`` fences).

    Required fields are emitted in stable order; unknown fields follow.
    """
    lines: list[str] = []

    # Required fields first, in stable order
    for key in REQUIRED_FIELDS:
        if key in data:
            _render_field(lines, key, data[key])

    # Unknown fields after required fields
    for key, value in data.items():
        if key not in REQUIRED_FIELDS:
            _render_field(lines, key, value)

    return "\n".join(lines) + "\n"


def _render_field(lines: list[str], key: str, value: object) -> None:
    if isinstance(value, list):
        lines.append(f"{key}:")
        for item in value:
            lines.append(f"  - {item}")
    elif value is None:
        lines.append(f"{key}:")
    else:
        lines.append(f"{key}: {value}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_metadata(
    data: dict[str, object], filename: str | None = None
) -> list[str]:
    """Return a list of error strings for invalid metadata.

    An empty list means the metadata is valid.
    """
    errors: list[str] = []

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # no point checking values if fields are missing

    # doc_type
    if data["doc_type"] not in ALLOWED_DOC_TYPES:
        errors.append(f"Invalid doc_type: {data['doc_type']}")

    # status
    if data["status"] not in ALLOWED_STATUSES:
        errors.append(f"Invalid status: {data['status']}")

    # audience values
    audience = data["audience"]
    if isinstance(audience, list):
        for val in audience:
            if val not in ALLOWED_AUDIENCES:
                errors.append(f"Invalid audience value: {val}")

    # Date format
    for field in ("created", "updated"):
        val = data.get(field)
        if val is not None and not _DATE_RE.match(str(val)):
            errors.append(f"Invalid date format for {field}: {val}")

    # List fields must be lists
    for field in LIST_FIELDS:
        if not isinstance(data.get(field), list):
            errors.append(f"{field} must be a list")

    return errors


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------

def repair_metadata(
    data: dict[str, object],
    filename: str,
    touch: bool = False,
) -> tuple[dict[str, object], bool]:
    """Return ``(repaired_metadata, changed)`` for *data*.

    *changed* is ``True`` when any field was added or corrected.
    When *touch* is ``True``, ``updated`` is always set to today.
    When any other field changes, ``updated`` is also bumped.
    """
    defaults = expected_metadata(filename)
    repaired: dict[str, object] = dict(data)
    changed = False
    today_str = _today()

    # --- scalar fields ---
    for field in ("title", "description", "doc_type", "status"):
        if field not in repaired or repaired[field] is None:
            repaired[field] = defaults[field]
            changed = True
        elif field == "doc_type" and repaired[field] not in ALLOWED_DOC_TYPES:
            repaired[field] = defaults[field]
            changed = True
        elif field == "status" and repaired[field] not in ALLOWED_STATUSES:
            repaired[field] = defaults[field]
            changed = True

    # --- created ---
    created_val = repaired.get("created")
    if created_val is None or not _DATE_RE.match(str(created_val)):
        repaired["created"] = today_str
        changed = True

    # --- updated ---
    updated_val = repaired.get("updated")
    updated_invalid = updated_val is None or not _DATE_RE.match(
        str(updated_val)
    )
    if updated_invalid:
        repaired["updated"] = today_str
        changed = True
    elif changed or touch:
        if repaired["updated"] != today_str:
            changed = True
        repaired["updated"] = today_str

    # --- list fields ---
    for field in LIST_FIELDS:
        if not isinstance(repaired.get(field), list):
            repaired[field] = list(defaults[field])
            changed = True

    # --- audience values ---
    if isinstance(repaired.get("audience"), list):
        invalid = [
            v for v in repaired["audience"] if v not in ALLOWED_AUDIENCES
        ]
        if invalid:
            repaired["audience"] = list(defaults["audience"])
            changed = True

    # If we changed anything above (and didn't already set updated), bump it
    if changed and repaired.get("updated") != today_str:
        repaired["updated"] = today_str

    return repaired, changed


# ---------------------------------------------------------------------------
# Ensure frontmatter (high-level: text in → text out)
# ---------------------------------------------------------------------------

def ensure_frontmatter(
    text: str,
    filename: str,
    touch: bool = False,
) -> tuple[str, str]:
    """Ensure *text* has valid frontmatter for *filename*.

    Returns ``(updated_text, status)`` where *status* is one of
    ``"added"``, ``"updated"``, ``"unchanged"``, or ``"created"``.
    """
    metadata, body, had_fm = parse_frontmatter(text)

    repaired, changed = repair_metadata(metadata, filename, touch=touch)

    if had_fm and not changed:
        return text, "unchanged"

    fm_str = render_frontmatter(repaired)
    new_text = f"---\n{fm_str}---\n"
    if body:
        if not body.startswith("\n"):
            new_text += "\n"
        new_text += body

    if not had_fm:
        status = "added"
    else:
        status = "updated"

    return new_text, status
