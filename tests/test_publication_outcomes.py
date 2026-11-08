"""Distinguish a saved file with cleanup failure from an unpublished write."""

import contextlib
import errno
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "project-memory/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import metadata
import path_safety
import repair_metadata
import setup_project_memory


class PublicationOutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def fail_task_temp_cleanup(self):
        original_unlink = os.unlink

        def unlink(path, *args, **kwargs):
            if str(path).startswith(".TASKS.md."):
                raise PermissionError(errno.EACCES, "injected temporary-file cleanup denial")
            return original_unlink(path, *args, **kwargs)

        return mock.patch.object(path_safety.os, "unlink", side_effect=unlink)

    def assert_valid(self, path: Path) -> None:
        values, _, had_frontmatter = metadata.parse_frontmatter(path.read_text(encoding="utf-8"))
        self.assertTrue(had_frontmatter)
        self.assertEqual(metadata.validate_metadata(values, path.name), [])

    def test_creation_cleanup_failure_has_a_published_outcome(self) -> None:
        with path_safety.open_project_directory(self.root, Path(".")) as directory_fd:
            with self.fail_task_temp_cleanup():
                with self.assertRaises(OSError) as raised:
                    path_safety.write_text_at(directory_fd, "TASKS.md", "TASKS.md", "saved", create=True)
        self.assertEqual(type(raised.exception).__name__, "PublishedCleanupError")
        self.assertEqual(raised.exception.relative_path, "TASKS.md")
        self.assertEqual(self.root.joinpath("TASKS.md").read_text(encoding="utf-8"), "saved")
        temporary = self.root / raised.exception.temporary_name
        self.assertEqual(temporary.stat().st_ino, self.root.joinpath("TASKS.md").stat().st_ino)

    def test_repair_reports_created_file_as_published_when_cleanup_fails(self) -> None:
        output = io.StringIO()
        with self.fail_task_temp_cleanup():
            with mock.patch.object(sys, "argv", ["repair_metadata.py", "--root", str(self.root)]):
                with contextlib.redirect_stdout(output):
                    code = repair_metadata.main()
        self.assertEqual(code, 1)
        self.assertIn("PUBLISHED: docs/TASKS.md", output.getvalue())
        self.assertIn("cleanup failed", output.getvalue())
        self.assertNotIn("SKIPPED: docs/TASKS.md", output.getvalue())
        for filename in metadata.MEMORY_FILES:
            self.assert_valid(self.root / "docs" / filename)

    def test_setup_reports_publication_before_cleanup_warning(self) -> None:
        previous = Path.cwd()
        output = io.StringIO()
        try:
            os.chdir(self.root)
            with self.fail_task_temp_cleanup():
                with contextlib.redirect_stdout(output):
                    code = setup_project_memory.main()
        finally:
            os.chdir(previous)
        self.assertEqual(code, 1)
        self.assertIn("Published docs/TASKS.md", output.getvalue())
        self.assertIn("cleanup failed", output.getvalue())
        self.assert_valid(self.root / "docs/TASKS.md")

    def test_migration_keeps_source_after_published_cleanup_failure(self) -> None:
        source = self.root / "TASKS.md"
        source.write_text("# Synthetic legacy body\n", encoding="utf-8")
        with self.fail_task_temp_cleanup():
            with self.assertRaises(OSError) as raised:
                setup_project_memory.migrate_legacy_files(self.root)
        self.assertEqual(type(raised.exception).__name__, "PublishedCleanupError")
        self.assertTrue(source.exists())
        self.assertIn("# Synthetic legacy body", self.root.joinpath("docs/TASKS.md").read_text(encoding="utf-8"))
        self.assert_valid(self.root / "docs/TASKS.md")

    def test_failure_before_publication_is_not_a_published_outcome(self) -> None:
        with path_safety.open_project_directory(self.root, Path(".")) as directory_fd:
            with mock.patch.object(path_safety.os, "link", side_effect=PermissionError(errno.EACCES, "injected publish denial")):
                with self.assertRaises(OSError) as raised:
                    path_safety.write_text_at(directory_fd, "TASKS.md", "TASKS.md", "unsaved", create=True)
        self.assertNotEqual(type(raised.exception).__name__, "PublishedCleanupError")
        self.assertEqual(list(self.root.iterdir()), [])

    @unittest.skipUnless(sys.platform == "darwin", "requires native Darwin deny-delete ACLs")
    def test_native_deny_delete_acl_reports_published_files(self) -> None:
        docs = self.root / "docs"
        docs.mkdir()

        def clear_fixture_acls():
            for path in [self.root, *self.root.rglob("*")]:
                subprocess.run(["chmod", "-N", str(path)], check=True)

        self.addCleanup(clear_fixture_acls)
        subprocess.run(["chmod", "+a", "everyone deny delete,file_inherit", str(docs)], check=True)
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["repair_metadata.py", "--root", str(self.root)]):
            with contextlib.redirect_stdout(output):
                code = repair_metadata.main()
        self.assertEqual(code, 1)
        self.assertNotIn("SKIPPED:", output.getvalue())
        self.assertEqual(output.getvalue().count("PUBLISHED:"), len(metadata.MEMORY_FILES))
        for filename in metadata.MEMORY_FILES:
            self.assert_valid(docs / filename)


if __name__ == "__main__":
    unittest.main()
