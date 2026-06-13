#!/usr/bin/env python3
"""Validate Project Memory Metadata v1 frontmatter on docs/ memory files.

Run from the target project root, or pass ``--root PATH``.
Exits 0 if all files pass, 1 if any fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metadata import (
    DOCS_DIR,
    MEMORY_FILES,
    parse_frontmatter,
    resolve_root,
    validate_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=None,
        help="Target project root (default: current working directory)",
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    docs_dir = root / DOCS_DIR
    any_fail = False

    for filename in MEMORY_FILES:
        rel = f"docs/{filename}"
        path = docs_dir / filename

        if not path.exists():
            print(f"ERROR: {rel}")
            print(f"- File does not exist")
            any_fail = True
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: {rel}")
            print(f"- Cannot read file: {exc}")
            any_fail = True
            continue

        try:
            metadata, _body, had_fm = parse_frontmatter(text)
        except ValueError as exc:
            print(f"ERROR: {rel}")
            print(f"- {exc}")
            any_fail = True
            continue

        if not had_fm:
            print(f"ERROR: {rel}")
            print(f"- No YAML frontmatter found")
            any_fail = True
            continue

        errors = validate_metadata(metadata, filename)
        if errors:
            print(f"ERROR: {rel}")
            for err in errors:
                print(f"- {err}")
            any_fail = True
        else:
            print(f"OK: {rel}")

    print()
    if any_fail:
        print("Metadata validation failed.")
        return 1

    print("Metadata validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
