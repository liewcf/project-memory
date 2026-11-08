"""Regression tests for concurrent edits between reading and publishing files."""

import contextlib
from datetime import date
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "project-memory" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import metadata
import path_safety
import repair_metadata
import setup_project_memory


class ReadVersionGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_repair_preserves_concurrent_task_changes_and_continues(self):
        for change in ("edit", "replace", "delete"):
            with self.subTest(change=change):
                with tempfile.TemporaryDirectory(dir=self.root) as directory:
                    root = Path(directory)
                    docs = root / "docs"
                    docs.mkdir()
                    tasks = docs / "TASKS.md"
                    initial = setup_project_memory.template_for("TASKS.md")
                    tasks.write_text(initial.replace(date.today().isoformat(), "2020-01-01"), encoding="utf-8")
                    later = docs / "CHANGELOG_WORK.md"
                    later.write_text("# Later file\n", encoding="utf-8")
                    changed = "# Concurrent user change\n"
                    original = repair_metadata.ensure_frontmatter

                    def mutate_after_read(text, filename, **kwargs):
                        result = original(text, filename, **kwargs)
                        if filename == "TASKS.md":
                            if change == "edit":
                                tasks.write_text(changed, encoding="utf-8")
                            elif change == "replace":
                                replacement = docs / "replacement"
                                replacement.write_text(changed, encoding="utf-8")
                                os.replace(replacement, tasks)
                            else:
                                tasks.unlink()
                        return result

                    output = io.StringIO()
                    with mock.patch.object(repair_metadata, "ensure_frontmatter", side_effect=mutate_after_read), \
                         mock.patch.object(sys, "argv", ["repair_metadata.py", "--root", str(root), "--touch"]), \
                         contextlib.redirect_stdout(output):
                        code = repair_metadata.main()
                    self.assertEqual(code, 1, output.getvalue())
                    if change == "delete":
                        self.assertFalse(tasks.exists())
                    else:
                        self.assertEqual(tasks.read_text(encoding="utf-8"), changed)
                    self.assertIn("SKIPPED: docs/TASKS.md", output.getvalue())
                    self.assertTrue(later.read_text(encoding="utf-8").startswith("---\n"))
                    self.assertEqual(list(docs.glob(".*.tmp")), [])
                    self.assertEqual(list(docs.glob(".TASKS.md.*")), [])

    def test_agents_refresh_preserves_concurrent_edits(self):
        for content in (
            "# Existing guidance\n",
            "# Existing guidance\n\n## Project Memory Requirement\n\nOld instructions.\n",
        ):
            with self.subTest(content=content):
                path = self.root / "AGENTS.md"
                path.write_text(content, encoding="utf-8")
                updated = content + "\nConcurrent user guidance.\n"
                original = setup_project_memory.has_project_memory_requirement

                def mutate_after_read(text):
                    result = original(text)
                    path.write_text(updated, encoding="utf-8")
                    return result

                with mock.patch.object(setup_project_memory, "has_project_memory_requirement", side_effect=mutate_after_read):
                    with self.assertRaises(path_safety.UnsafeProjectPath):
                        setup_project_memory.ensure_agents_requirement(self.root, path)
                self.assertEqual(path.read_text(encoding="utf-8"), updated)
                self.assertEqual(list(self.root.glob(".AGENTS.md.*")), [])


if __name__ == "__main__":
    unittest.main()
