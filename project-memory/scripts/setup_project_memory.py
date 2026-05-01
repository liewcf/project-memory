#!/usr/bin/env python3
"""Initialize repo-level project memory files for Codex.

Run this script from the root of a software project or repository.
It is safe to run repeatedly: existing files are preserved, and the
AGENTS.md memory requirement is appended only when missing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path


MEMORY_FILES = (
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "DECISIONS.md",
    "TASKS.md",
    "CHANGELOG_WORK.md",
)

AGENTS_REQUIREMENT_HEADING = "## Project Memory Requirement"
AGENTS_REQUIREMENT = f"""{AGENTS_REQUIREMENT_HEADING}

Keep these repo-level memory files accurate and concise when work changes project context:

- `PROJECT_CONTEXT.md` for stable project facts, architecture, workflows, and constraints.
- `DECISIONS.md` for dated technical or product decisions and rationale.
- `TASKS.md` for current tasks, blockers, and next actions.
- `CHANGELOG_WORK.md` for dated notes on changed files, behavior, docs, config, dependencies, tooling, tests, and verification.

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

## Current

- [ ] Confirm project purpose, build/test commands, and active priorities.

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


def has_project_memory_requirement(content: str) -> bool:
    lowered = content.lower()
    return (
        "project memory requirement" in lowered
        or (
            "project_context.md" in lowered
            and "decisions.md" in lowered
            and "tasks.md" in lowered
            and "changelog_work.md" in lowered
        )
    )


def ensure_agents_requirement(path: Path) -> str:
    content = read_text(path)
    if has_project_memory_requirement(content):
        return "unchanged"

    separator = "\n\n" if content.rstrip() else ""
    updated = f"{content.rstrip()}{separator}{AGENTS_REQUIREMENT}\n"
    path.write_text(updated, encoding="utf-8")
    return "updated"


def main() -> int:
    root = Path.cwd()
    created: list[str] = []
    existing: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []

    for filename in MEMORY_FILES:
        path = root / filename
        if path.exists():
            existing.append(filename)
            continue

        path.write_text(template_for(filename), encoding="utf-8")
        created.append(filename)

    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        result = ensure_agents_requirement(agents_path)
        if result == "updated":
            updated.append("AGENTS.md")
        else:
            unchanged.append("AGENTS.md")

    print("Project memory setup summary")
    print(f"Root: {root}")
    print(f"Created: {', '.join(created) if created else 'none'}")
    print(f"Updated: {', '.join(updated) if updated else 'none'}")
    print(f"Existing: {', '.join(existing) if existing else 'none'}")
    print(f"Unchanged: {', '.join(unchanged) if unchanged else 'none'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
