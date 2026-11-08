"""Preserve file access controls and extended attributes through safe descriptors."""

from __future__ import annotations

import ctypes
import errno
import os
import stat
import sys


def copy_file_metadata(source_fd: int, destination_fd: int) -> None:
    """Copy security metadata, or fail before the destination is published.

    Darwin ACLs are replaced exactly through descriptor-based ACL APIs;
    fcopyfile(3) copies xattrs without changing data or modification time.
    Linux exposes ACLs as xattrs.
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
        library = ctypes.CDLL(None, use_errno=True)
        fcopyfile = library.fcopyfile
        get_acl = library.acl_get_fd_np
        init_acl = library.acl_init
        set_acl = library.acl_set_fd_np
        free_acl = library.acl_free
    except (OSError, AttributeError) as exc:
        raise OSError("descriptor-safe metadata preservation is unavailable") from exc
    fcopyfile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    fcopyfile.restype = ctypes.c_int
    get_acl.argtypes = [ctypes.c_int, ctypes.c_int]
    get_acl.restype = ctypes.c_void_p
    init_acl.argtypes = [ctypes.c_int]
    init_acl.restype = ctypes.c_void_p
    set_acl.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    set_acl.restype = ctypes.c_int
    free_acl.argtypes = [ctypes.c_void_p]
    free_acl.restype = ctypes.c_int

    acl_type_extended = 0x100  # Darwin sys/acl.h.
    source_acl = get_acl(source_fd, acl_type_extended)
    if not source_acl:
        if ctypes.get_errno() != errno.ENOENT:
            _raise_native_error()
        # No source ACL must clear any ACL inherited by the staging file.
        source_acl = init_acl(0)
        if not source_acl:
            _raise_native_error()
    try:
        if set_acl(destination_fd, source_acl, acl_type_extended) != 0:
            _raise_native_error()
        copyfile_xattr = 1 << 2
        if fcopyfile(source_fd, destination_fd, None, copyfile_xattr) != 0:
            _raise_native_error()
    finally:
        free_acl(source_acl)


def _raise_native_error() -> None:
    error = ctypes.get_errno() or errno.EIO
    raise OSError(error, os.strerror(error))


def _copy_linux_metadata(source_fd: int, destination_fd: int) -> None:
    if not all(hasattr(os, name) for name in ("listxattr", "getxattr", "setxattr", "removexattr")):
        raise OSError("descriptor-safe metadata preservation is unavailable")
    source_names = set(os.listxattr(source_fd))
    for name in set(os.listxattr(destination_fd)) - source_names:
        os.removexattr(destination_fd, name)
    for name in source_names:
        os.setxattr(destination_fd, name, os.getxattr(source_fd, name))
