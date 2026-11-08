"""Shared path-safety helpers for project-memory writers."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from enum import Enum, auto
import errno
import os
from pathlib import Path
import stat
from typing import Iterator
from uuid import uuid4

from file_metadata import copy_file_metadata


_DIR_FD_OPERATIONS = (os.open, os.stat, os.rename, os.link, os.unlink)
_NOFOLLOW_OPERATIONS = (os.stat, os.link)


class UnsafeProjectPath(RuntimeError):
    """Raised when a project-memory path cannot be opened safely."""


class PublishedCleanupError(OSError):
    """The destination was saved, but its temporary hard link remains."""

    def __init__(self, relative_path: str, temporary_name: str, cleanup_error: OSError):
        self.relative_path = relative_path
        self.temporary_name = temporary_name
        self.cleanup_error = cleanup_error
        message = (
            f"Published {relative_path}; temporary-file cleanup failed for "
            f"{temporary_name}: {cleanup_error}"
        )
        if cleanup_error.errno is None:
            super().__init__(message)
        else:
            super().__init__(cleanup_error.errno, message)


class _PublicationState(Enum):
    STAGED = auto()
    PUBLISHED_WITH_TEMP = auto()
    PUBLISHED = auto()


def ensure_safe_project_path(root: Path, path: Path) -> Path:
    """Reject symlinks and paths that resolve outside *root*."""
    root_path = root.resolve()
    candidate = path if path.is_absolute() else root / path

    if candidate.is_symlink():
        raise UnsafeProjectPath(
            f"Refusing to use symlinked project memory path: {path}"
        )

    try:
        candidate.resolve(strict=False).relative_to(root_path)
    except ValueError as exc:
        raise UnsafeProjectPath(
            f"Refusing to use project memory path outside project root: {path}"
        ) from exc

    return candidate


def descriptor_safety_supported() -> bool:
    """Return whether this runtime exposes the required no-follow primitives."""
    return (
        hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_DIRECTORY")
        and all(operation in os.supports_dir_fd for operation in _DIR_FD_OPERATIONS)
        and all(operation in os.supports_follow_symlinks for operation in _NOFOLLOW_OPERATIONS)
    )


def _require_descriptor_safety() -> None:
    if not descriptor_safety_supported():
        raise UnsafeProjectPath(
            "race-safe descriptor-relative no-follow operations are unavailable"
        )


def _raise_open_error(relative_path: str, exc: OSError) -> None:
    if exc.errno in {errno.ELOOP, errno.EMLINK, errno.ENOTDIR}:
        raise UnsafeProjectPath(
            f"Refusing to use symlinked project memory path: {relative_path}"
        ) from exc
    raise exc


@contextmanager
def open_project_directory(
    root: Path, relative_path: Path, *, create: bool = False
) -> Iterator[int]:
    """Open a project directory without following its final path component."""
    _require_descriptor_safety()
    path = ensure_safe_project_path(root, relative_path)
    if create:
        path.mkdir(exist_ok=True)

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        _raise_open_error(str(relative_path), exc)

    try:
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def open_project_file(
    directory_fd: int, filename: str, relative_path: str, *, writable: bool = False
) -> Iterator[int]:
    """Keep a no-follow regular-file descriptor open until its operation ends."""
    _require_descriptor_safety()
    try:
        descriptor = os.open(
            filename,
            (os.O_RDWR if writable else os.O_RDONLY) | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory_fd,
        )
    except OSError as exc:
        _raise_open_error(relative_path, exc)

    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise UnsafeProjectPath(f"Refusing non-regular project memory file: {relative_path}")
        yield descriptor
    finally:
        os.close(descriptor)


def read_text_at(directory_fd: int, filename: str, relative_path: str) -> str:
    """Read UTF-8 text relative to an already-open safe directory."""
    with open_project_file(directory_fd, filename, relative_path) as descriptor:
        with os.fdopen(descriptor, "r", encoding="utf-8", closefd=False) as handle:
            return handle.read()


def file_version(info: os.stat_result) -> tuple[int, int, int, int, int]:
    """Identify content changes without treating a read's access time as an edit."""
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def write_text_at(
    directory_fd: int,
    filename: str,
    relative_path: str,
    text: str,
    *,
    create: bool,
    metadata_fd: int | None = None,
) -> None:
    """Stage complete UTF-8 text, then publish it without following the target.

    Creation publishes with an exclusive link; replacement uses atomic rename.
    Failures before publication leave the destination untouched. This is a
    per-file boundary, not a transaction across a whole setup or repair run.
    """
    _require_descriptor_safety()
    with ExitStack() as stack:
        if not create:
            metadata_fd = stack.enter_context(
                open_project_file(directory_fd, filename, relative_path, writable=True)
            )
        _stage_and_publish(directory_fd, filename, relative_path, text, create, metadata_fd)


def _stage_and_publish(
    directory_fd: int, filename: str, relative_path: str, text: str,
    create: bool, metadata_fd: int | None,
) -> None:
    previous = os.fstat(metadata_fd) if metadata_fd is not None else None
    temporary = f".{filename}.{uuid4().hex}.tmp"
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o666, dir_fd=directory_fd,
    )
    state = _PublicationState.STAGED

    try:
        try:
            default_mode = stat.S_IMODE(os.fstat(descriptor).st_mode)
            os.fchmod(descriptor, 0o600)
            handle = os.fdopen(descriptor, "w", encoding="utf-8")
        except BaseException:
            os.close(descriptor)
            raise
        with handle as stream:
            if metadata_fd is not None:
                copy_file_metadata(metadata_fd, stream.fileno())
                os.fchmod(stream.fileno(), 0o600)
            stream.write(text)
            stream.flush()
            if metadata_fd is not None:
                copy_file_metadata(metadata_fd, stream.fileno())
            else:
                os.fchmod(stream.fileno(), default_mode)
            os.fsync(stream.fileno())

        if create:
            try:
                os.link(
                    temporary, filename, src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd, follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise UnsafeProjectPath(
                    f"Refusing to replace unexpected project memory path: {relative_path}"
                ) from exc
            state = _PublicationState.PUBLISHED_WITH_TEMP
        else:
            with open_project_file(directory_fd, filename, relative_path, writable=True) as current_fd:
                current = os.fstat(current_fd)
            assert previous is not None
            if file_version(current) != file_version(previous):
                raise UnsafeProjectPath(f"Project memory file changed during write: {relative_path}")
            os.rename(temporary, filename, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            state = _PublicationState.PUBLISHED
    finally:
        if state is not _PublicationState.PUBLISHED:
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                if state is _PublicationState.PUBLISHED_WITH_TEMP:
                    raise PublishedCleanupError(relative_path, temporary, exc) from exc
                raise


def write_project_text(root: Path, path: Path, text: str, *, create: bool) -> None:
    """Use the same publication boundary for setup's project-relative writes."""
    path = ensure_safe_project_path(root, path)
    with open_project_directory(root, path.parent.relative_to(root)) as directory_fd:
        write_text_at(directory_fd, path.name, str(path.relative_to(root)), text, create=create)
