"""Failure and publication boundaries for descriptor-relative writes."""

from contextlib import contextmanager
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "project-memory/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import path_safety


class AtomicWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.context = path_safety.open_project_directory(self.root, Path("."))
        self.fd = self.context.__enter__()

    def tearDown(self) -> None:
        self.context.__exit__(None, None, None)
        self.tmp.cleanup()

    def write(self, text: str, *, create: bool) -> None:
        path_safety.write_text_at(self.fd, "TASKS.md", "TASKS.md", text, create=create)

    def test_failed_write_preserves_existing_or_missing_target(self) -> None:
        original_fdopen = os.fdopen

        @contextmanager
        def failing_writer(*args, **kwargs):
            with original_fdopen(*args, **kwargs) as handle:
                class PartialWriter:
                    def fileno(self):
                        return handle.fileno()

                    def write(self, text):
                        handle.write(text[:3])
                        handle.flush()
                        raise OSError("injected partial write")

                yield PartialWriter()

        for create in (True, False):
            with self.subTest(create=create):
                target = self.root / "TASKS.md"
                if not create:
                    target.write_text("original", encoding="utf-8")
                with mock.patch.object(path_safety.os, "fdopen", failing_writer):
                    with self.assertRaisesRegex(OSError, "partial write"):
                        self.write("replacement", create=create)
                if create:
                    self.assertEqual(list(self.root.iterdir()), [])
                else:
                    self.assertEqual(target.read_text(encoding="utf-8"), "original")
                    self.assertEqual(list(self.root.iterdir()), [target])

    def test_failed_publication_preserves_existing_target(self) -> None:
        target = self.root / "TASKS.md"
        target.write_text("original", encoding="utf-8")
        with mock.patch.object(path_safety.os, "rename", side_effect=OSError("publish failed")):
            with self.assertRaisesRegex(OSError, "publish failed"):
                self.write("replacement", create=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertEqual(list(self.root.iterdir()), [target])

    def test_create_does_not_clobber_a_target_that_appears(self) -> None:
        original_link = os.link
        target = self.root / "TASKS.md"

        def competing_create(*args, **kwargs):
            target.write_text("other writer", encoding="utf-8")
            return original_link(*args, **kwargs)

        with mock.patch.object(path_safety.os, "link", side_effect=competing_create):
            with self.assertRaises(path_safety.UnsafeProjectPath):
                self.write("replacement", create=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "other writer")
        self.assertEqual(list(self.root.iterdir()), [target])

    def test_replacement_preserves_permissions_and_does_not_modify_hard_links(self) -> None:
        target = self.root / "TASKS.md"
        target.write_text("original", encoding="utf-8")
        target.chmod(0o640)
        alias = self.root / "alias.md"
        alias.hardlink_to(target)
        self.write("replacement", create=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "replacement")
        self.assertEqual(alias.read_text(encoding="utf-8"), "original")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)

    def test_replacement_refuses_a_target_changed_during_staging(self) -> None:
        target = self.root / "TASKS.md"
        target.write_text("original", encoding="utf-8")
        original_fsync = os.fsync

        def competing_edit(descriptor):
            target.write_text("other writer's longer content", encoding="utf-8")
            return original_fsync(descriptor)

        with mock.patch.object(path_safety.os, "fsync", side_effect=competing_edit):
            with self.assertRaisesRegex(path_safety.UnsafeProjectPath, "changed during write"):
                self.write("replacement", create=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "other writer's longer content")
        self.assertEqual(list(self.root.iterdir()), [target])

    def test_failed_flush_keeps_destination_unchanged(self) -> None:
        target = self.root / "TASKS.md"
        target.write_text("original", encoding="utf-8")
        with mock.patch.object(path_safety.os, "fsync", side_effect=OSError("flush failed")):
            with self.assertRaisesRegex(OSError, "flush failed"):
                self.write("replacement", create=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertEqual(list(self.root.iterdir()), [target])

    def test_missing_safety_primitives_fail_before_creating_files(self) -> None:
        with mock.patch.object(path_safety, "descriptor_safety_supported", return_value=False):
            with self.assertRaisesRegex(path_safety.UnsafeProjectPath, "unavailable"):
                self.write("replacement", create=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_failed_metadata_copy_keeps_existing_destination(self) -> None:
        target = self.root / "TASKS.md"
        target.write_text("original", encoding="utf-8")
        with mock.patch.object(path_safety, "copy_file_metadata", side_effect=OSError("metadata failed")):
            with self.assertRaisesRegex(OSError, "metadata failed"):
                self.write("replacement", create=False)
        self.assertEqual(target.read_text(encoding="utf-8"), "original")
        self.assertEqual(list(self.root.iterdir()), [target])

    def test_replacement_requires_an_existing_regular_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.write("replacement", create=False)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_symlink_is_rejected_without_modifying_its_target(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("original", encoding="utf-8")
        (self.root / "TASKS.md").symlink_to(outside)
        with self.assertRaises(path_safety.UnsafeProjectPath):
            self.write("replacement", create=False)
        self.assertEqual(outside.read_text(encoding="utf-8"), "original")


if __name__ == "__main__":
    unittest.main()
