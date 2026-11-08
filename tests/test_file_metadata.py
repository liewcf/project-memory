"""Real filesystem metadata must survive replacement and legacy migration."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "project-memory/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import path_safety
import setup_project_memory


@unittest.skipUnless(sys.platform in {"darwin", "linux"}, "requires supported filesystem metadata APIs")
class MetadataPreservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "TASKS.md"
        self.source.write_text("# Original body\n", encoding="utf-8")
        self.source.chmod(0o640)
        self.attribute = "com.example.project-memory-test" if sys.platform == "darwin" else "user.project_memory_test"
        if sys.platform == "darwin":
            subprocess.run(["chmod", "+a", "user:daemon deny read", str(self.source)], check=True)
            subprocess.run(["xattr", "-w", self.attribute, "preserved", str(self.source)], check=True)
        else:
            os.setxattr(self.source, self.attribute, b"preserved")
        self.original_metadata = self.metadata(self.source)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def metadata(self, path: Path):
        info = path.stat()
        if sys.platform == "darwin":
            acl = subprocess.run(["ls", "-le", str(path)], check=True, capture_output=True, text=True).stdout.splitlines()[1:]
            attribute = subprocess.run(["xattr", "-p", self.attribute, str(path)], check=True, capture_output=True).stdout.strip()
        else:
            acl = None
            attribute = os.getxattr(path, self.attribute)
        return info.st_uid, info.st_gid, info.st_mode & 0o7777, acl, attribute

    def test_replacement_preserves_owner_permissions_acl_and_xattrs(self) -> None:
        with path_safety.open_project_directory(self.root, Path(".")) as directory_fd:
            path_safety.write_text_at(directory_fd, "TASKS.md", "TASKS.md", "replacement", create=False)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "replacement")
        self.assertEqual(self.metadata(self.source), self.original_metadata)

    def test_migration_preserves_owner_permissions_acl_and_xattrs(self) -> None:
        migrated, conflicts = setup_project_memory.migrate_legacy_files(self.root)
        self.assertEqual(migrated, ["TASKS.md"])
        self.assertEqual(conflicts, [])
        self.assertFalse(self.source.exists())
        destination = self.root / "docs/TASKS.md"
        self.assertIn("# Original body", destination.read_text(encoding="utf-8"))
        self.assertEqual(self.metadata(destination), self.original_metadata)


if __name__ == "__main__":
    unittest.main()
