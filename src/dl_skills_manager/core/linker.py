"""Cross-platform symlink management."""

__all__ = [
    "create_link",
    "is_link_valid",
    "remove_link",
]

import errno
import shutil
import sys
from enum import IntEnum
from pathlib import Path

from dl_skills_manager.core.exceptions import LinkError


class WindowsError(IntEnum):
    """Windows error codes for privilege/access issues."""

    ACCESS_DENIED = 5
    PRIVILEGE_NOT_HELD = 1314


def _is_permission_error(e: OSError) -> bool:
    """Check if OSError is permission-related on Windows."""
    # On Windows, symlink creation can fail with EACCES or EPERM for non-admin users
    # Check standard errno values first
    if e.errno in (errno.EACCES,):
        return True
    # Check EPERM if it exists (may not be defined on Windows)
    eperm = getattr(errno, "EPERM", None)
    if eperm is not None and e.errno == eperm:
        return True
    # Windows-specific: symlink privilege error (error codes stored in exception args)
    if sys.platform == "win32" and e.winerror is not None:
        return e.winerror in (
            WindowsError.ACCESS_DENIED,
            WindowsError.PRIVILEGE_NOT_HELD,
        )
    return False


def _resolve_source(source: Path) -> Path:
    """Resolve source path, following any symlinks.

    This ensures we work with the actual directory, not a symlink to it.

    Args:
        source: Path to resolve.

    Returns:
        Resolved Path object.

    Raises:
        LinkError: If source is a symlink but target does not exist.
    """
    # If source itself is a symlink, resolve to the real path
    if source.is_symlink():
        resolved = source.resolve()
        if not resolved.exists():
            msg = f"Source symlink target does not exist: {source} -> {resolved}"
            raise LinkError(msg)
        return resolved
    return source


def create_link(source: Path, target: Path, *, force: bool = False) -> None:
    """Create a symlink from source to target.

    On Windows, if symlink fails due to permission issues, falls back to
    copying the directory. Other OS errors (e.g., filesystem doesn't support
    symlinks) are raised directly.

    Args:
        source: Source directory to link to.
        target: Target path for the link.
        force: If True, remove existing target before creating link.

    Raises:
        LinkError: If the operation fails.
    """
    # Resolve any symlinks in source before operations
    source = _resolve_source(source)

    if not source.exists():
        raise LinkError(f"Source does not exist: {source}")

    if target.is_symlink() or target.exists():
        if force:
            remove_link(target)
        else:
            raise LinkError(f"Target already exists: {target}")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
    except OSError as e:
        # Only fallback to copy for permission-related errors
        # Other errors (e.g., filesystem doesn't support symlinks) should propagate
        if _is_permission_error(e):
            try:
                # When force=True, target was already removed by remove_link above
                # so we use dirs_exist_ok=False to ensure clean copy
                shutil.copytree(source, target)
            except OSError as copy_err:
                raise LinkError(f"Failed to create link: {copy_err}") from copy_err
            # Fallback copy succeeded, return successfully
            return
        # Re-raise with more context for non-permission errors
        raise LinkError(
            f"Failed to create symlink (not a permission issue): {e}"
        ) from e


def remove_link(target: Path) -> None:
    """Remove a symlink or copied directory.

    Args:
        target: Target path to remove.

    Raises:
        LinkError: If the removal fails.
    """
    if not target.exists() and not target.is_symlink():
        raise LinkError(f"Target does not exist: {target}")

    try:
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    except OSError as e:
        raise LinkError(f"Failed to remove {target}: {e}") from e


def is_link_valid(target: Path) -> bool:
    """Check if a symlink points to a valid target or copied directory exists.

    Args:
        target: Path to check.

    Returns:
        True if target is a valid symlink pointing to existing path,
        or if target is a directory containing a valid skill (has SKILL.md).
        Returns False if target does not exist.
    """
    if not target.exists():
        return False
    if target.is_symlink():
        return target.resolve().exists()
    # For copied directories, verify it contains expected skill content
    if target.is_dir():
        return target.joinpath("SKILL.md").exists()
    return False
