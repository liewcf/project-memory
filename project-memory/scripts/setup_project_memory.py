#!/usr/bin/env python3
"""Initialize project-level memory files for Codex.

Run this script from the root of a project folder or repository.
It is safe to run repeatedly: existing files are preserved, and the
AGENTS.md memory requirement is added or refreshed when needed.
"""

from __future__ import annotations

from datetime import date
from enum import Enum, auto
import os
from pathlib import Path
import re

from metadata import (
    DOCS_DIR,
    MEMORY_FILES,
    expected_metadata,
    ensure_frontmatter,
    parse_frontmatter,
    render_frontmatter,
)
from path_safety import (
    PublishedCleanupError,
    UnsafeProjectPath,
    ensure_safe_project_path,
    file_version,
    open_project_directory,
    open_project_file,
    read_text_at,
    write_project_text,
    write_text_at,
)

LEGACY_ROOT_FILES = MEMORY_FILES


class MemoryLocation(Enum):
    ABSENT = auto()
    LEGACY_ONLY = auto()
    DOCS_ONLY = auto()
    CONFLICT = auto()


def memory_location(legacy_path: Path, docs_path: Path) -> MemoryLocation:
    if legacy_path.exists():
        return MemoryLocation.CONFLICT if docs_path.exists() else MemoryLocation.LEGACY_ONLY
    return MemoryLocation.DOCS_ONLY if docs_path.exists() else MemoryLocation.ABSENT

AGENTS_REQUIREMENT_HEADING = "## Project Memory Requirement"
AGENTS_REQUIREMENT_PATTERN = re.compile(
    r"(?ms)^##\s+Project Memory Requirement\s*\n.*?(?=^##\s+|\Z)",
    re.IGNORECASE,
)
AGENTS_REQUIREMENT_LINES = (
    AGENTS_REQUIREMENT_HEADING,
    "",
    (
        "Keep these project memory files accurate and concise when work changes "
        "durable context in project folders or repositories:"
    ),
    "",
    "- `docs/PROJECT_CONTEXT.md` for stable project facts, structure, workflows, resources, and constraints.",
    "- `docs/DECISIONS.md` for dated project, product, technical, process, or content decisions and rationale.",
    "- `docs/TASKS.md` for current tasks, blockers, and next actions.",
    (
        "- `docs/CHANGELOG_WORK.md` for dated notes on changed files, docs, assets, "
        "behavior, deliverables, process, tooling, checks, and verification."
    ),
    "",
    (
        "Do not store secrets, credentials, API keys, private tokens, database dumps, "
        "or sensitive personal data in project memory."
    ),
    "",
    (
        "docs/*.md memory files use Project Memory Metadata v1 frontmatter; "
        "preserve it when editing. AGENTS.md stays plain Markdown."
    ),
)
AGENTS_REQUIREMENT = "\n".join(AGENTS_REQUIREMENT_LINES) + "\n"

AGENTS_REQUIREMENT_REQUIRED_PHRASES = (
    "project folders or repositories",
    "docs/project_context.md",
    "stable project facts, structure, workflows, resources, and constraints",
    "docs/decisions.md",
    "project, product, technical, process, or content decisions",
    "docs/tasks.md",
    "docs/changelog_work.md",
    (
        "changed files, docs, assets, behavior, deliverables, process, tooling, "
        "checks, and verification"
    ),
    "do not store secrets",
    "project memory metadata v1 frontmatter",
    "agents.md stays plain markdown",
)


def today() -> str:
    return date.today().isoformat()


def template_for(filename: str) -> str:
    current_date = today()

    if filename == "AGENTS.md":
        return f"# Agent Instructions\n\n{AGENTS_REQUIREMENT}\n"

    # Build rich body for docs/ memory files
    bodies = {
        "PROJECT_CONTEXT.md": """# Project Context

## Overview

- Project purpose: Unknown.
- Primary users: Unknown.
- Current status: Unknown.

## Project Structure

- Unknown.

## Key Workflows

- Important commands or checks: Unknown.
- Review method: Unknown.
- Acceptance criteria: Unknown.

## Constraints

- Do not assume framework, deployment, package manager, infrastructure, or domain
  details until verified from project evidence.
""",
        "DECISIONS.md": f"""# Decisions

## {current_date}

- Initialized project memory. No major project, product, technical, process, or content decisions recorded yet.
""",
        "TASKS.md": """# Tasks

## Recommended Next Action

- Confirm project purpose, key workflows, review checks, and active priorities.

## Current

- [ ] Confirm project purpose, key workflows, review checks, and active priorities.

## Verification

- Not yet verified against project evidence.

## Blockers

- None recorded.

## Done

- None recorded.
""",
        "CHANGELOG_WORK.md": f"""# Work Changelog

## {current_date}

- Initialized project memory files.
""",
    }

    body = bodies[filename]
    fm = render_frontmatter(expected_metadata(filename))
    return f"---\n{fm}---\n\n{body}"


def has_project_memory_requirement(content: str) -> bool:
    match = AGENTS_REQUIREMENT_PATTERN.search(content)
    if not match:
        return False

    lowered = match.group(0).lower()
    return all(phrase in lowered for phrase in AGENTS_REQUIREMENT_REQUIRED_PHRASES)


def ensure_agents_requirement(root: Path, path: Path) -> str:
    path = ensure_safe_project_path(root, path)
    with open_project_directory(root, path.parent.relative_to(root)) as directory_fd:
        content = read_text_at(directory_fd, path.name, str(path.relative_to(root)))
    if has_project_memory_requirement(content):
        return "unchanged"

    if AGENTS_REQUIREMENT_PATTERN.search(content):
        updated = AGENTS_REQUIREMENT_PATTERN.sub(
            f"{AGENTS_REQUIREMENT.rstrip()}\n\n", content.rstrip(), count=1
        )
        write_project_text(root, path, f"{updated.rstrip()}\n", create=False)
        return "updated"

    separator = "\n\n" if content.rstrip() else ""
    updated = f"{content.rstrip()}{separator}{AGENTS_REQUIREMENT}\n"
    write_project_text(root, path, updated, create=False)
    return "updated"


def migrate_legacy_files(root: Path) -> tuple[list[str], list[str]]:
    """Move legacy root memory files to docs/ if docs/ versions don't exist."""
    migrated: list[str] = []
    left_in_place: list[str] = []
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)

    with open_project_directory(root, Path(".")) as root_fd:
        with open_project_directory(root, DOCS_DIR, create=True) as docs_fd:
            for filename in LEGACY_ROOT_FILES:
                legacy_path = ensure_safe_project_path(root, Path(filename))
                docs_path = ensure_safe_project_path(root, docs_dir / filename)
                location = memory_location(legacy_path, docs_path)
                if location is MemoryLocation.CONFLICT:
                    left_in_place.append(filename)
                    continue
                if location is not MemoryLocation.LEGACY_ONLY:
                    continue

                with open_project_file(root_fd, filename, filename) as source_fd:
                    source = os.fstat(source_fd)
                    with os.fdopen(source_fd, "r", encoding="utf-8", closefd=False) as handle:
                        content = handle.read()
                    _meta, _body, had_fm = parse_frontmatter(content)
                    if not had_fm:
                        content, _ = ensure_frontmatter(content, filename, touch=False)

                    # Publish the complete docs copy before removing the source.
                    write_text_at(
                        docs_fd, filename, f"docs/{filename}", content,
                        create=True, metadata_fd=source_fd,
                    )
                current = os.stat(filename, dir_fd=root_fd, follow_symlinks=False)
                if file_version(current) != file_version(source):
                    raise UnsafeProjectPath(f"Legacy memory file changed during migration: {filename}")
                os.unlink(filename, dir_fd=root_fd)
                migrated.append(filename)

    return migrated, left_in_place


def ensure_docs_memory_files(root: Path, docs_dir: Path) -> tuple[list[str], list[str]]:
    created: list[str] = []
    existing: list[str] = []

    docs_dir.mkdir(exist_ok=True)

    for filename in MEMORY_FILES:
        path = ensure_safe_project_path(root, docs_dir / filename)
        if path.exists():
            existing.append(filename)
            continue

        write_project_text(root, path, template_for(filename), create=True)
        created.append(filename)

    return created, existing


def ensure_agents_file(root: Path) -> tuple[str, str]:
    agents_path = ensure_safe_project_path(root, Path("AGENTS.md"))
    if not agents_path.exists():
        write_project_text(root, agents_path, template_for("AGENTS.md"), create=True)
        return "created", "AGENTS.md"

    return ensure_agents_requirement(root, agents_path), "AGENTS.md"


def print_summary(
    root: Path,
    migrated: list[str],
    legacy_left_in_place: list[str],
    created: list[str],
    updated: list[str],
    existing: list[str],
    unchanged: list[str],
) -> None:
    def show(items: list[str]) -> str:
        return ", ".join(items) if items else "none"

    print("Project memory setup summary")
    print(f"Root: {root}")
    if migrated:
        print(f"Migrated from root: {show(migrated)}")
    if legacy_left_in_place:
        print(f"Legacy root files left in place: {show(legacy_left_in_place)}")
    print(f"Created: {show(created)}")
    print(f"Updated: {show(updated)}")
    print(f"Existing: {show(existing)}")
    print(f"Unchanged: {show(unchanged)}")


def preflight_setup(root: Path) -> None:
    """Reject known unsafe paths and malformed migrations before any writes."""
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)
    agents_path = ensure_safe_project_path(root, Path("AGENTS.md"))
    with open_project_directory(root, Path(".")) as root_fd:
        if agents_path.exists():
            read_text_at(root_fd, "AGENTS.md", "AGENTS.md")
        if docs_dir.exists() and not docs_dir.is_dir():
            raise UnsafeProjectPath("Project memory docs/ path is not a directory")
        for filename in MEMORY_FILES:
            docs_path = ensure_safe_project_path(root, docs_dir / filename)
            legacy_path = ensure_safe_project_path(root, Path(filename))
            if docs_path.exists() and not docs_path.is_file():
                raise UnsafeProjectPath(f"Project memory path is not a file: docs/{filename}")
            if memory_location(legacy_path, docs_path) is MemoryLocation.LEGACY_ONLY:
                parse_frontmatter(read_text_at(root_fd, filename, filename))


def main() -> int:
    root = Path.cwd()
    preflight_setup(root)
    try:
        migrated, legacy_left_in_place = migrate_legacy_files(root)
        docs_dir = ensure_safe_project_path(root, DOCS_DIR)
        created, existing = ensure_docs_memory_files(root, docs_dir)
        agents_status, agents_name = ensure_agents_file(root)
    except PublishedCleanupError as exc:
        print(f"WARNING: {exc}")
        return 1
    updated: list[str] = []
    unchanged: list[str] = []
    if agents_status == "created":
        created.append(agents_name)
    elif agents_status == "updated":
        updated.append(agents_name)
    else:
        unchanged.append(agents_name)

    print_summary(
        root,
        migrated,
        legacy_left_in_place,
        created,
        updated,
        existing,
        unchanged,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
