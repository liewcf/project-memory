"""Integration tests for the validate_metadata.py CLI script."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "project-memory" / "scripts"
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_metadata.py"


def _run_validate(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_valid_docs(docs_dir: Path) -> None:
    """Write all four docs files with valid frontmatter."""
    today = date.today().isoformat()
    files = {
        "PROJECT_CONTEXT.md": (
            f"---\ntitle: Project Context\ndescription: Stable facts.\n"
            f"doc_type: context\nstatus: stable\ncreated: {today}\n"
            f"updated: {today}\ntags:\n  - project-memory\naudience:\n  - agent\n"
            f"related:\n  - DECISIONS.md\n---\n\n# Project Context\n"
        ),
        "DECISIONS.md": (
            f"---\ntitle: Decisions\ndescription: Decision log.\n"
            f"doc_type: decision_log\nstatus: active\ncreated: {today}\n"
            f"updated: {today}\ntags:\n  - decisions\naudience:\n  - agent\n"
            f"related:\n  - PROJECT_CONTEXT.md\n---\n\n# Decisions\n"
        ),
        "TASKS.md": (
            f"---\ntitle: Current Tasks\ndescription: Task state.\n"
            f"doc_type: task_state\nstatus: active\ncreated: {today}\n"
            f"updated: {today}\ntags:\n  - tasks\naudience:\n  - agent\n"
            f"related:\n  - PROJECT_CONTEXT.md\n---\n\n# Current Tasks\n"
        ),
        "CHANGELOG_WORK.md": (
            f"---\ntitle: Work Changelog\ndescription: Work log.\n"
            f"doc_type: work_log\nstatus: active\ncreated: {today}\n"
            f"updated: {today}\ntags:\n  - changelog\naudience:\n  - agent\n"
            f"related:\n  - PROJECT_CONTEXT.md\n---\n\n# Work Changelog\n"
        ),
    }
    for name, content in files.items():
        (docs_dir / name).write_text(content, encoding="utf-8")


class ValidateMetadataCwdTests(unittest.TestCase):
    """Tests using cwd (no --root)."""

    def setUp(self) -> None:
        self._prev_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        Path("docs").mkdir()

    def tearDown(self) -> None:
        os.chdir(self._prev_cwd)
        self._tmp.cleanup()

    def test_valid_files_pass(self) -> None:
        _write_valid_docs(Path("docs"))
        result = _run_validate()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Metadata validation passed.", result.stdout)

    def test_missing_file_fails(self) -> None:
        result = _run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Metadata validation failed.", result.stdout)

    def test_no_frontmatter_fails(self) -> None:
        for fn in ("PROJECT_CONTEXT.md", "DECISIONS.md", "TASKS.md", "CHANGELOG_WORK.md"):
            (Path("docs") / fn).write_text(f"# {fn}\n", encoding="utf-8")
        result = _run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No YAML frontmatter found", result.stdout)

    def test_missing_required_field_fails(self) -> None:
        today = date.today().isoformat()
        # Write TASKS.md with missing 'updated' field
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndoc_type: task_state\nstatus: active\n"
            f"created: {today}\ntags:\n  - tasks\naudience:\n  - agent\n"
            f"related:\n  - x\n---\n# Tasks\n",
            encoding="utf-8",
        )
        _write_valid_docs(Path("docs"))
        # Overwrite just TASKS.md
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndoc_type: task_state\nstatus: active\n"
            f"created: {today}\ntags:\n  - tasks\naudience:\n  - agent\n"
            f"related:\n  - x\n---\n# Tasks\n",
            encoding="utf-8",
        )
        result = _run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required field: updated", result.stdout)

    def test_invalid_doc_type_fails(self) -> None:
        _write_valid_docs(Path("docs"))
        today = date.today().isoformat()
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: wrong\n"
            f"status: active\ncreated: {today}\nupdated: {today}\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"---\n# Tasks\n",
            encoding="utf-8",
        )
        result = _run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid doc_type: wrong", result.stdout)

    def test_invalid_date_format_fails(self) -> None:
        _write_valid_docs(Path("docs"))
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: task_state\n"
            f"status: active\ncreated: June 13\nupdated: 2026-01-01\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"---\n# Tasks\n",
            encoding="utf-8",
        )
        result = _run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid date format", result.stdout)

    def test_agents_md_ignored(self) -> None:
        """AGENTS.md is not validated even if it exists."""
        _write_valid_docs(Path("docs"))
        Path("AGENTS.md").write_text("# Agents\nNo frontmatter.\n", encoding="utf-8")
        result = _run_validate()
        self.assertEqual(result.returncode, 0)


class ValidateMetadataRootTests(unittest.TestCase):
    """Tests using --root PATH."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "docs").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_root_flag_validates_provided_root(self) -> None:
        _write_valid_docs(self.root / "docs")
        result = _run_validate("--root", str(self.root))
        self.assertEqual(result.returncode, 0)
        self.assertIn("Metadata validation passed.", result.stdout)

    def test_root_flag_fails_for_bad_root(self) -> None:
        result = _run_validate("--root", str(self.root))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
