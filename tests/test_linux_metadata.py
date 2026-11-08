"""Native Linux ACL, xattr and ownership checks included in unittest discovery."""

from __future__ import annotations

import errno
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "project-memory/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import file_metadata
import path_safety
import setup_project_memory


ACL_NAME = "system.posix_acl_access"
ATTRIBUTE = "user.project_memory_linux_test"
UNDEFINED_ID = 0xFFFFFFFF
UNSUPPORTED_XATTR_ERRORS = {errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}


def acl_bytes(*, directory: bool = False) -> bytes:
    # Linux UAPI: include/uapi/linux/{posix_acl,posix_acl_xattr}.h.
    # user_obj, named user, group_obj, mask, other; entries are little-endian.
    other_uid = 65534 if os.geteuid() != 65534 else 65533
    entries = [
        (0x01, 7 if directory else 6, UNDEFINED_ID),
        (0x02, 4, other_uid),
        (0x04, 0, UNDEFINED_ID),
        (0x10, 4, UNDEFINED_ID),
        (0x20, 0, UNDEFINED_ID),
    ]
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)


def attributes(path: Path) -> dict[str, bytes]:
    return {name: os.getxattr(path, name) for name in os.listxattr(path)}


def metadata(path: Path) -> tuple[int, int, int, dict[str, bytes]]:
    info = path.stat()
    return info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode), attributes(path)


@unittest.skipUnless(sys.platform == "linux", "requires native Linux ACL/xattr APIs")
class LinuxMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        required_apis = ("listxattr", "getxattr", "setxattr", "removexattr")
        if not all(hasattr(os, name) for name in required_apis):
            self.skipTest("Linux xattr APIs are unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="linux-metadata-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Isolate new files from any default ACL inherited through TMPDIR.
        try:
            os.removexattr(self.root, "system.posix_acl_default")
        except OSError as exc:
            if exc.errno in UNSUPPORTED_XATTR_ERRORS:
                self.skipTest(f"Fixture filesystem does not support default ACLs: {exc}")
            if exc.errno != errno.ENODATA:
                raise

    def set_fixture_xattr(self, path: Path, name: str, value: bytes) -> None:
        try:
            os.setxattr(path, name, value)
        except OSError as exc:
            if exc.errno in UNSUPPORTED_XATTR_ERRORS:
                self.skipTest(f"Fixture filesystem does not support {name}: {exc}")
            raise

    def make_source(self, path: Path | None = None, *, with_acl: bool = True) -> Path:
        path = path or self.root / "TASKS.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Synthetic private body\n", encoding="utf-8")
        path.chmod(0o640)
        self.set_fixture_xattr(path, ATTRIBUTE, b"preserved\x00binary\xff")
        if with_acl:
            self.set_fixture_xattr(path, ACL_NAME, acl_bytes())
            self.assertEqual(os.getxattr(path, ACL_NAME), acl_bytes())
        else:
            self.assertNotIn(ACL_NAME, os.listxattr(path))
        return path

    def replace(self, path: Path, text: str = "replacement\n") -> None:
        directory = path.parent.relative_to(self.root)
        with path_safety.open_project_directory(self.root, directory) as directory_fd:
            path_safety.write_text_at(
                directory_fd, path.name, str(path.relative_to(self.root)), text, create=False
            )

    def test_native_acl_and_binary_xattrs_survive_replacement(self) -> None:
        path = self.make_source()
        before = metadata(path)
        self.replace(path)
        self.assertEqual(path.read_text(encoding="utf-8"), "replacement\n")
        self.assertEqual(metadata(path), before)

    def test_native_acl_and_binary_xattrs_survive_migration(self) -> None:
        path = self.make_source()
        before = metadata(path)
        migrated, conflicts = setup_project_memory.migrate_legacy_files(self.root)
        self.assertEqual(migrated, ["TASKS.md"])
        self.assertFalse(conflicts)
        self.assertFalse(path.exists())
        target = self.root / "docs/TASKS.md"
        self.assertIn("# Synthetic private body", target.read_text(encoding="utf-8"))
        self.assertEqual(metadata(target), before)

    def test_repair_cli_preserves_acl_and_is_idempotent(self) -> None:
        path = self.make_source(self.root / "docs/TASKS.md")
        before = metadata(path)
        command = [sys.executable, str(SCRIPTS_DIR / "repair_metadata.py"), "--root", str(self.root)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(metadata(path), before)
        content = path.read_bytes()
        inode = path.stat().st_ino

        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(metadata(path), before)
        self.assertEqual(path.read_bytes(), content)
        self.assertEqual(path.stat().st_ino, inode)

    def test_setup_cli_preserves_acl_during_migration(self) -> None:
        path = self.make_source()
        before = metadata(path)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "setup_project_memory.py")],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(path.exists())
        self.assertEqual(metadata(self.root / "docs/TASKS.md"), before)

    def test_supplementary_group_ownership_survives_replacement(self) -> None:
        groups = sorted((set(os.getgroups()) | {os.getgid()}) - {os.getegid()})
        if not groups:
            self.skipTest("requires a supplementary group different from the effective group")
        # Avoid an inherited setgid directory making new files use the test group already.
        self.root.chmod(0o700)
        path = self.make_source()
        os.chown(path, -1, groups[0])
        before = metadata(path)
        self.replace(path)
        self.assertEqual(metadata(path), before)
        self.assertEqual(path.stat().st_gid, groups[0])

    def test_restrictive_acl_mask_survives_replacement(self) -> None:
        path = self.make_source()
        path.chmod(0o600)
        before = metadata(path)
        self.assertIn(ACL_NAME, before[3])
        self.replace(path)
        self.assertEqual(metadata(path), before)

    def test_inherited_acl_is_removed_when_source_has_no_acl(self) -> None:
        path = self.make_source(with_acl=False)
        before = metadata(path)
        self.set_fixture_xattr(self.root, "system.posix_acl_default", acl_bytes(directory=True))
        probe = self.root / "inherited-probe"
        probe.write_text("synthetic probe", encoding="utf-8")
        self.assertIn(ACL_NAME, os.listxattr(probe))
        self.replace(path)
        self.assertEqual(metadata(path), before)
        self.assertNotIn(ACL_NAME, os.listxattr(path))

    def test_stale_destination_xattrs_are_removed(self) -> None:
        source = self.make_source()
        destination = self.root / "staged"
        destination.write_text("staged content", encoding="utf-8")
        self.set_fixture_xattr(destination, "user.stale", b"remove me")
        with source.open("rb") as src, destination.open("r+b") as dst:
            file_metadata.copy_file_metadata(src.fileno(), dst.fileno())
        self.assertEqual(metadata(destination), metadata(source))
        self.assertEqual(destination.read_text(encoding="utf-8"), "staged content")

    def test_unsupported_xattr_read_preserves_existing_file(self) -> None:
        path = self.make_source()
        before, content = metadata(path), path.read_bytes()
        error = OSError(errno.EOPNOTSUPP, "injected unsupported xattr")
        with mock.patch.object(file_metadata.os, "getxattr", side_effect=error):
            with self.assertRaises(OSError):
                self.replace(path)
        self.assertEqual(path.read_bytes(), content)
        self.assertEqual(metadata(path), before)
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_metadata_failure_after_data_write_preserves_existing_file(self) -> None:
        path = self.make_source()
        before, content = metadata(path), path.read_bytes()
        original = file_metadata._copy_linux_metadata
        calls = 0

        def fail_second_copy(source_fd: int, destination_fd: int) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise PermissionError(errno.EPERM, "injected metadata write denial")
            original(source_fd, destination_fd)

        with mock.patch.object(file_metadata, "_copy_linux_metadata", side_effect=fail_second_copy):
            with self.assertRaises(PermissionError):
                self.replace(path)
        self.assertEqual(calls, 2)
        self.assertEqual(path.read_bytes(), content)
        self.assertEqual(metadata(path), before)
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_failed_migration_keeps_source_with_metadata(self) -> None:
        path = self.make_source()
        before, content = metadata(path), path.read_bytes()
        error = PermissionError(errno.EPERM, "injected denial")
        with mock.patch.object(file_metadata, "_copy_linux_metadata", side_effect=error):
            with self.assertRaises(PermissionError):
                setup_project_memory.migrate_legacy_files(self.root)
        self.assertEqual(path.read_bytes(), content)
        self.assertEqual(metadata(path), before)
        self.assertEqual(list((self.root / "docs").iterdir()), [])

    def test_negative_control_detects_acl_and_xattr_loss(self) -> None:
        path = self.make_source()
        before = metadata(path)

        def mode_only_copy(source_fd: int, destination_fd: int) -> None:
            os.fchmod(destination_fd, stat.S_IMODE(os.fstat(source_fd).st_mode))

        with mock.patch.object(path_safety, "copy_file_metadata", side_effect=mode_only_copy):
            self.replace(path)
        self.assertNotEqual(metadata(path), before)
        self.assertNotIn(ACL_NAME, attributes(path))
        self.assertNotIn(ATTRIBUTE, attributes(path))


if __name__ == "__main__":
    unittest.main()
