#!/usr/bin/env python3
"""Initialize repo-level project memory files for Codex.

Run this script from the root of a software project or repository.
It is safe to run repeatedly: existing files are preserved, and the
AGENTS.md memory requirement is added or refreshed when needed.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re


DOCS_DIR = Path("docs")
MEMORY_FILES = (
    "PROJECT_CONTEXT.md",
    "DECISIONS.md",
    "TASKS.md",
    "CHANGELOG_WORK.md",
)

LEGACY_ROOT_FILES = (
    "PROJECT_CONTEXT.md",
    "DECISIONS.md",
    "TASKS.md",
    "CHANGELOG_WORK.md",
)

AGENTS_REQUIREMENT_HEADING = "## Project Memory Requirement"
AGENTS_REQUIREMENT_PATTERN = re.compile(
    r"(?ms)^##\s+Project Memory Requirement\s*\n.*?(?=^##\s+|\Z)",
    re.IGNORECASE,
)
AGENTS_REQUIREMENT = f"""{AGENTS_REQUIREMENT_HEADING}

Keep these repo-level memory files accurate and concise when work changes project context:

- `docs/PROJECT_CONTEXT.md` for stable project facts, architecture, workflows, and constraints.
- `docs/DECISIONS.md` for dated technical or product decisions and rationale.
- `docs/TASKS.md` for current tasks, blockers, and next actions.
- `docs/CHANGELOG_WORK.md` for dated notes on changed files, behavior, docs, config, dependencies, tooling, tests, and verification.

Do not store secrets, credentials, API keys, private tokens, database dumps, or sensitive personal data in project memory.
"""


def today() -> str:
    return date.today().isoformat()


def template_for(filename: str) -> str:
    current_date = today()

    templates = {
        "AGENTS.md": f"""# Agent Instructions

{AGENTS_REQUIREMENT}
""",
        "PROJECT_CONTEXT.md": """# Project Context

## Overview

- Project purpose: Unknown.
- Primary users: Unknown.
- Current status: Unknown.

## Architecture

- Unknown.

## Development Workflow

- Package manager: Unknown.
- Build command: Unknown.
- Test command: Unknown.
- Run command: Unknown.

## Constraints

- Do not assume framework, deployment, package manager, or infrastructure details until verified from repo evidence.
""",
        "DECISIONS.md": f"""# Decisions

## {current_date}

- Initialized project memory. No major technical or product decisions recorded yet.
""",
        "TASKS.md": """# Tasks

## Recommended Next Action

- Confirm project purpose, build/test commands, and active priorities.

## Current

- [ ] Confirm project purpose, build/test commands, and active priorities.

## Verification

- Not yet verified against repo evidence.

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

    return templates[filename]


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
    return (
        "docs/project_context.md" in lowered
        and "docs/decisions.md" in lowered
        and "docs/tasks.md" in lowered
        and "docs/changelog_work.md" in lowered
    )


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


def migrate_legacy_files(root: Path) -> list[str]:
    """Move legacy root memory files to docs/ if docs/ versions don't exist."""
    migrated: list[str] = []
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)

    docs_dir.mkdir(exist_ok=True)

    for filename in LEGACY_ROOT_FILES:
        legacy_path = root / filename
        docs_path = ensure_safe_project_path(root, docs_dir / filename)

        if legacy_path.exists() and not docs_path.exists():
            ensure_safe_project_path(root, legacy_path)
            legacy_path.rename(docs_path)
            migrated.append(filename)

    return migrated


def main() -> int:
    root = Path.cwd()
    created: list[str] = []
    existing: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []

    migrated = migrate_legacy_files(root)
    docs_dir = ensure_safe_project_path(root, DOCS_DIR)

    docs_dir.mkdir(exist_ok=True)

    for filename in MEMORY_FILES:
        path = ensure_safe_project_path(root, docs_dir / filename)
        if path.exists():
            existing.append(filename)
            continue

        path.write_text(template_for(filename), encoding="utf-8")
        created.append(filename)

    agents_path = ensure_safe_project_path(root, Path("AGENTS.md"))
    if not agents_path.exists():
        agents_path.write_text(template_for("AGENTS.md"), encoding="utf-8")
        created.append("AGENTS.md")
    else:
        result = ensure_agents_requirement(root, agents_path)
        if result == "updated":
            updated.append("AGENTS.md")
        else:
            unchanged.append("AGENTS.md")

    print("Project memory setup summary")
    print(f"Root: {root}")
    if migrated:
        print(f"Migrated from root: {', '.join(migrated)}")
    print(f"Created: {', '.join(created) if created else 'none'}")
    print(f"Updated: {', '.join(updated) if updated else 'none'}")
    print(f"Existing: {', '.join(existing) if existing else 'none'}")
    print(f"Unchanged: {', '.join(unchanged) if unchanged else 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
