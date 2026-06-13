#!/usr/bin/env python3
"""Repair Project Memory Metadata v1 frontmatter on docs/ memory files.

Run from the target project root, or pass ``--root PATH``.
Use ``--touch`` to bump the ``updated`` date even when nothing else changes.

Exits 0 on success, 1 if any file could not be repaired.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metadata import (
    DOCS_DIR,
    MEMORY_FILES,
    default_body,
    ensure_frontmatter,
    parse_frontmatter,
    render_frontmatter,
    expected_metadata,
    resolve_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Target project root (default: current working directory)",
    )
    parser.add_argument(
        "--touch",
        action="store_true",
        help="Bump updated date even when no other changes are needed",
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    docs_dir = root / DOCS_DIR
    had_error = False

    # Ensure docs/ directory exists
    try:
        docs_dir.mkdir(exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create docs/ directory: {exc}")
        return 1

    for filename in MEMORY_FILES:
        rel = f"docs/{filename}"
        path = docs_dir / filename

        if not path.exists():
            # Create file with default frontmatter + minimal body
            fm = render_frontmatter(expected_metadata(filename))
            body = default_body(filename)
            content = f"---\n{fm}---\n\n{body}"
            try:
                path.write_text(content, encoding="utf-8")
                print(f"Created metadata: {rel}")
            except OSError as exc:
                print(f"SKIPPED: {rel} (cannot write: {exc})")
                had_error = True
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"SKIPPED: {rel} (cannot read: {exc})")
            had_error = True
            continue

        try:
            updated_text, status = ensure_frontmatter(
                text, filename, touch=args.touch
            )
        except ValueError as exc:
            print(f"SKIPPED: {rel} ({exc})")
            had_error = True
            continue

        if status == "unchanged":
            print(f"Skipped unchanged: {rel}")
        else:
            try:
                path.write_text(updated_text, encoding="utf-8")
            except OSError as exc:
                print(f"SKIPPED: {rel} (cannot write: {exc})")
                had_error = True
                continue

            if status == "added":
                print(f"Added metadata: {rel}")
            else:
                print(f"Updated metadata: {rel}")

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
