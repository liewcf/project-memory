#!/usr/bin/env python3
"""Initialize project-level memory files for Codex.

Run this script from the root of a project folder or repository.
It is safe to run repeatedly: existing files are preserved, and the
AGENTS.md memory requirement is added or refreshed when needed.
"""

from __future__ import annotations

from datetime import date
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

LEGACY_ROOT_FILES = MEMORY_FILES

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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def ensure_safe_project_path(root: Path, path: Path) -> Path:
    root_path = root.resolve()
    candidate = path if path.is_absolute() else root / path

    if candidate.is_symlink():
        raise RuntimeError(f"Refusing to use symlinked project memory path: {path}")

    try:
        candidate.resolve(strict=False).relative_to(root_path)
    except ValueError as exc:
        raise RuntimeError(
            f"Refusing to use project memory path outside project root: {path}"
        ) from exc

    return candidate


def has_project_memory_requirement(content: str) -> bool:
    match = AGENTS_REQUIREMENT_PATTERN.search(content)
    if not match:
        return False

    lowered = match.group(0).lower()
    return all(phrase in lowered for phrase in AGENTS_REQUIREMENT_REQUIRED_PHRASES)


def ensure_agents_requirement(root: Path, path: Path) -> str:
    path = ensure_safe_project_path(root, path)
    content = read_text(path)
    if has_project_memory_requirement(content):
        return "unchanged"

    if AGENTS_REQUIREMENT_PATTERN.search(content):
        updated = AGENTS_REQUIREMENT_PATTERN.sub(
            f"{AGENTS_REQUIREMENT.rstrip()}\n\n", content.rstrip(), count=1
        )
        path.write_text(f"{updated.rstrip()}\n", encoding="utf-8")
        return "updated"

    separator = "\n\n" if content.rstrip() else ""
    updated = f"{content.rstrip()}{separator}{AGENTS_REQUIREMENT}\n"
    path.write_text(updated, encoding="utf-8")
    return "updated"


def migrate_legacy_files(root: Path) -> tuple[list[str], list[str]]:
    """Move legacy root memory files to docs/ if docs/ versions don't exist."""
    migrated: list[str] = []
    left_in_place: list[str] = []
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)

    docs_dir.mkdir(exist_ok=True)

    for filename in LEGACY_ROOT_FILES:
        legacy_path = root / filename
        docs_path = ensure_safe_project_path(root, docs_dir / filename)

        if legacy_path.exists() and not docs_path.exists():
            ensure_safe_project_path(root, legacy_path)
            legacy_path.rename(docs_path)
            # Prepend frontmatter to migrated file if it lacks it
            content = read_text(docs_path)
            _meta, _body, had_fm = parse_frontmatter(content)
            if not had_fm:
                updated_text, _ = ensure_frontmatter(
                    content, filename, touch=False
                )
                docs_path.write_text(updated_text, encoding="utf-8")
            migrated.append(filename)
        elif legacy_path.exists() and docs_path.exists():
            left_in_place.append(filename)

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

        path.write_text(template_for(filename), encoding="utf-8")
        created.append(filename)

    return created, existing


def ensure_agents_file(root: Path) -> tuple[str, str]:
    agents_path = ensure_safe_project_path(root, Path("AGENTS.md"))
    if not agents_path.exists():
        agents_path.write_text(template_for("AGENTS.md"), encoding="utf-8")
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


def main() -> int:
    root = Path.cwd()
    migrated, legacy_left_in_place = migrate_legacy_files(root)
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)
    created, existing = ensure_docs_memory_files(root, docs_dir)
    updated: list[str] = []
    unchanged: list[str] = []

    agents_status, agents_name = ensure_agents_file(root)
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
