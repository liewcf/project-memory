"""Integration tests for the repair_metadata.py CLI script."""

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
REPAIR_SCRIPT = SCRIPTS_DIR / "repair_metadata.py"
VALIDATE_SCRIPT = SCRIPTS_DIR / "validate_metadata.py"


def _run_repair(
    *args: str, cwd: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPAIR_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _run_validate(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class RepairMetadataCwdTests(unittest.TestCase):
    """Tests using cwd (no --root)."""

    def setUp(self) -> None:
        self._prev_cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        Path("docs").mkdir()

    def tearDown(self) -> None:
        os.chdir(self._prev_cwd)
        self._tmp.cleanup()

    def test_creates_missing_files(self) -> None:
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        for fn in (
            "PROJECT_CONTEXT.md",
            "DECISIONS.md",
            "TASKS.md",
            "CHANGELOG_WORK.md",
        ):
            with self.subTest(filename=fn):
                path = Path("docs") / fn
                self.assertTrue(path.exists())
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"))

    def test_adds_frontmatter_to_plain_markdown(self) -> None:
        (Path("docs") / "TASKS.md").write_text(
            "# Tasks\n\n- Item 1\n", encoding="utf-8"
        )
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("# Tasks", content)
        self.assertIn("- Item 1", content)

    def test_preserves_existing_body(self) -> None:
        today = date.today().isoformat()
        body = "# My Tasks\n\n- Special item\n- Another item\n"
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: task_state\n"
            f"status: active\ncreated: {today}\nupdated: {today}\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"---\n\n{body}",
            encoding="utf-8",
        )
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn("Special item", content)
        self.assertIn("Another item", content)

    def test_idempotent_without_touch(self) -> None:
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        # Second run should skip all files
        result2 = _run_repair()
        self.assertEqual(result2.returncode, 0)
        self.assertIn("Skipped unchanged", result2.stdout)
        self.assertNotIn("Updated metadata", result2.stdout)

    def test_touch_bumps_updated(self) -> None:
        old_date = "2020-01-01"
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: task_state\n"
            f"status: active\ncreated: {old_date}\nupdated: {old_date}\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"---\n\n# Tasks\n",
            encoding="utf-8",
        )
        # First repair without touch should preserve old updated
        _run_repair()
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn(f"updated: {old_date}", content)
        # Touch run should bump updated to today
        result2 = _run_repair("--touch")
        self.assertEqual(result2.returncode, 0)
        content2 = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn(f"updated: {date.today().isoformat()}", content2)

    def test_updated_preserved_without_touch(self) -> None:
        today = date.today().isoformat()
        old_date = "2020-01-01"
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: task_state\n"
            f"status: active\ncreated: {old_date}\nupdated: {old_date}\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"---\n\n# Tasks\n",
            encoding="utf-8",
        )
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn(f"updated: {old_date}", content)

    def test_repaired_output_passes_validation(self) -> None:
        """After repair, validate should pass."""
        _run_repair()
        result = _run_validate()
        self.assertEqual(result.returncode, 0)
        self.assertIn("Metadata validation passed.", result.stdout)

    def test_agents_md_ignored(self) -> None:
        Path("AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        _run_repair()
        content = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(content, "# Agents\n")
        self.assertFalse(content.startswith("---"))

    def test_preserves_unknown_fields(self) -> None:
        today = date.today().isoformat()
        (Path("docs") / "TASKS.md").write_text(
            f"---\ntitle: Tasks\ndescription: d\ndoc_type: task_state\n"
            f"status: active\ncreated: {today}\nupdated: {today}\n"
            f"tags:\n  - t\naudience:\n  - agent\nrelated:\n  - x\n"
            f"custom_field: my_value\n---\n\n# Tasks\n",
            encoding="utf-8",
        )
        result = _run_repair()
        self.assertEqual(result.returncode, 0)
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        self.assertIn("custom_field: my_value", content)

    def test_stable_field_order(self) -> None:
        _run_repair()
        content = (Path("docs") / "TASKS.md").read_text(encoding="utf-8")
        # Extract frontmatter keys in order
        lines = content.split("\n")
        keys = []
        in_fm = False
        for line in lines:
            if line == "---":
                if in_fm:
                    break
                in_fm = True
                continue
            if in_fm and ":" in line and not line.startswith("  "):
                keys.append(line.split(":")[0])
        expected = [
            "title", "description", "doc_type", "status",
            "created", "updated", "tags", "audience", "related",
        ]
        self.assertEqual(keys, expected)


class RepairMetadataRootTests(unittest.TestCase):
    """Tests using --root PATH."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "docs").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_root_flag_repairs_provided_root(self) -> None:
        (self.root / "docs" / "TASKS.md").write_text(
            "# Current Tasks\n\n- Confirm metadata.\n", encoding="utf-8"
        )
        result = _run_repair("--root", str(self.root))
        self.assertEqual(result.returncode, 0)
        content = (self.root / "docs" / "TASKS.md").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn("Confirm metadata.", content)

    def test_root_flag_creates_missing_files(self) -> None:
        result = _run_repair("--root", str(self.root))
        self.assertEqual(result.returncode, 0)
        for fn in (
            "PROJECT_CONTEXT.md",
            "DECISIONS.md",
            "TASKS.md",
            "CHANGELOG_WORK.md",
        ):
            self.assertTrue(
                (self.root / "docs" / fn).exists(),
                f"docs/{fn} should be created under --root",
            )

    def test_root_flag_validates_after_repair(self) -> None:
        _run_repair("--root", str(self.root))
        result = _run_validate("--root", str(self.root))
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
