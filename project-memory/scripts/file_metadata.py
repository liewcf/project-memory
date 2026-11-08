"""Preserve file access controls and extended attributes through safe descriptors."""

from __future__ import annotations

import ctypes
import os
import stat
import sys


def copy_file_metadata(source_fd: int, destination_fd: int) -> None:
    """Copy security metadata, or fail before the destination is published.

    Darwin stores ACLs outside Python's POSIX interfaces. Its fcopyfile(3)
    accepts already-open descriptors; COPYFILE_ACL | COPYFILE_XATTR leaves
    file contents and modification time alone. Linux exposes ACLs as xattrs.
    """
    if sys.platform not in {"darwin", "linux"}:
        raise OSError("descriptor-safe metadata preservation is unavailable")
    source = os.fstat(source_fd)
    destination = os.fstat(destination_fd)
    if (source.st_uid, source.st_gid) != (destination.st_uid, destination.st_gid):
        os.fchown(destination_fd, source.st_uid, source.st_gid)
    os.fchmod(destination_fd, stat.S_IMODE(source.st_mode))

    if sys.platform == "darwin":
        _copy_darwin_metadata(source_fd, destination_fd)
    else:
        _copy_linux_metadata(source_fd, destination_fd)


def _copy_darwin_metadata(source_fd: int, destination_fd: int) -> None:
    try:
        fcopyfile = ctypes.CDLL(None, use_errno=True).fcopyfile
    except (OSError, AttributeError) as exc:
        raise OSError("descriptor-safe metadata preservation is unavailable") from exc
    fcopyfile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    fcopyfile.restype = ctypes.c_int
    copyfile_acl = 1 << 0
    copyfile_xattr = 1 << 2
    if fcopyfile(source_fd, destination_fd, None, copyfile_acl | copyfile_xattr) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _copy_linux_metadata(source_fd: int, destination_fd: int) -> None:
    if not all(hasattr(os, name) for name in ("listxattr", "getxattr", "setxattr", "removexattr")):
        raise OSError("descriptor-safe metadata preservation is unavailable")
    source_names = set(os.listxattr(source_fd))
    for name in set(os.listxattr(destination_fd)) - source_names:
        os.removexattr(destination_fd, name)
    for name in source_names:
        os.setxattr(destination_fd, name, os.getxattr(source_fd, name))
