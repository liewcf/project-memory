"""Default Project Memory metadata values."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path


DOCS_DIR = Path("docs")

MEMORY_FILES: tuple[str, ...] = (
    "PROJECT_CONTEXT.md",
    "DECISIONS.md",
    "TASKS.md",
    "CHANGELOG_WORK.md",
)

EXPECTED_DOC_TYPES: dict[str, str] = {
    "PROJECT_CONTEXT.md": "context",
    "DECISIONS.md": "decision_log",
    "TASKS.md": "task_state",
    "CHANGELOG_WORK.md": "work_log",
}

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


def today() -> str:
    return date.today().isoformat()


def expected_metadata(filename: str) -> dict[str, object]:
    """Return fresh default metadata for *filename*."""
    current_date = today()
    templates: dict[str, dict[str, object]] = {
        "PROJECT_CONTEXT.md": {
            "title": "Project Context",
            "description": "Stable project facts, structure, workflows, resources, and constraints.",
            "doc_type": EXPECTED_DOC_TYPES["PROJECT_CONTEXT.md"],
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
            "doc_type": EXPECTED_DOC_TYPES["DECISIONS.md"],
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "decisions", "rationale"],
            "audience": ["agent", "maintainer"],
            "related": ["PROJECT_CONTEXT.md", "TASKS.md", "CHANGELOG_WORK.md"],
        },
        "TASKS.md": {
            "title": "Current Tasks",
            "description": "Current tasks, blockers, verification state, and recommended next actions.",
            "doc_type": EXPECTED_DOC_TYPES["TASKS.md"],
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "tasks", "current-state"],
            "audience": ["agent", "maintainer"],
            "related": ["PROJECT_CONTEXT.md", "DECISIONS.md", "CHANGELOG_WORK.md"],
        },
        "CHANGELOG_WORK.md": {
            "title": "Work Changelog",
            "description": "Dated notes on changed files, deliverables, tooling, checks, and verification.",
            "doc_type": EXPECTED_DOC_TYPES["CHANGELOG_WORK.md"],
            "status": "active",
            "created": current_date,
            "updated": current_date,
            "tags": ["project-memory", "changelog", "work-log", "verification"],
            "audience": ["agent", "maintainer"],
            "related": ["PROJECT_CONTEXT.md", "DECISIONS.md", "TASKS.md"],
        },
    }
    return dict(templates[filename])


MINIMAL_BODIES: dict[str, str] = {
    "PROJECT_CONTEXT.md": "# Project Context\n\nNo durable context recorded yet.\n",
    "DECISIONS.md": "# Decisions\n\nNo decisions recorded yet.\n",
    "TASKS.md": "# Current Tasks\n\nNo current tasks recorded yet.\n",
    "CHANGELOG_WORK.md": "# Work Changelog\n\nNo work log entries recorded yet.\n",
}


def default_body(filename: str) -> str:
    return MINIMAL_BODIES[filename]


def resolve_root(root_arg: str | None = None) -> Path:
    if root_arg is not None:
        return Path(root_arg)
    return Path(os.getcwd())
