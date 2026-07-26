"""Shared path-safety helpers for project-memory writers."""

from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
from typing import Iterator


class UnsafeProjectPath(RuntimeError):
    """Raised when a project-memory path cannot be opened safely."""


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
        and os.open in os.supports_dir_fd
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


def read_text_at(directory_fd: int, filename: str, relative_path: str) -> str:
    """Read UTF-8 text relative to an already-open safe directory."""
    _require_descriptor_safety()
    try:
        descriptor = os.open(
            filename,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        raise
    except OSError as exc:
        _raise_open_error(relative_path, exc)

    with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
        return handle.read()


def write_text_at(
    directory_fd: int,
    filename: str,
    relative_path: str,
    text: str,
    *,
    create: bool,
) -> None:
    """Create or replace UTF-8 text without following the target path."""
    _require_descriptor_safety()
    flags = os.O_WRONLY | os.O_NOFOLLOW
    if create:
        flags |= os.O_CREAT | os.O_EXCL

    try:
        descriptor = os.open(filename, flags, 0o666, dir_fd=directory_fd)
    except FileExistsError as exc:
        raise UnsafeProjectPath(
            f"Refusing to replace unexpected project memory path: {relative_path}"
        ) from exc
    except OSError as exc:
        _raise_open_error(relative_path, exc)

    try:
        if not create:
            os.ftruncate(descriptor, 0)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
