"""Shared utilities for CLI commands.

Provides common functionality used across multiple commands such as
repository path resolution, skill directory lookup, and version parsing.
"""

import dataclasses
import logging
import os
import shutil
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast, overload

import tomli_w

from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.exceptions import (
    LinkError,
    SkillNotFoundError,
    ValidationError,
    VersionNotFoundError,
    WriteError,
)
from dl_skills_manager.core.linker import copy_skill_dir

logger = logging.getLogger(__name__)

__all__ = [
    "atomic_write_toml",
    "find_skill_dir",
    "find_version_dir",
    "get_latest_file_timestamp",
    "install_skill_copy",
    "resolve_skills_target_dir",
    "update_skill_copy",
    "validate_skill_name",
]


def get_latest_file_timestamp(skill_dir: Path) -> str:
    """Get timestamp from the most recently modified file in the directory.

    Args:
        skill_dir: Directory to scan.

    Returns:
        Timestamp string in format 'YYYYMMDDHHMMSS'.
    """
    latest_mtime = 0.0
    for file_path in skill_dir.rglob("*"):
        if file_path.is_file():
            mtime = file_path.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime

    dt = datetime.fromtimestamp(latest_mtime, tz=UTC)
    return dt.strftime("%Y%m%d%H%M%S")


def validate_skill_name(name: str) -> None:
    """Validate skill name format.

    Args:
        name: Skill name to validate.

    Raises:
        ValidationError: If skill name contains invalid characters or patterns.
    """
    # Check path traversal patterns first for proper error messages
    if ".." in name or name.startswith(("~", "/", "\\", "$")):
        raise ValidationError(f"Invalid skill name: {name}")
    if "/" in name or "\\" in name:
        raise ValidationError(f"Invalid skill name: {name}")
    if not all(c.isalnum() or c in "-_" for c in name):
        raise ValidationError(
            "Skill name must be alphanumeric, hyphens, or underscores"
        )


def find_skill_dir(name: str, *, config: SkillSyncConfig | None = None) -> Path:
    """Find skill directory in repository.

    Args:
        name: Skill name.
        config: Optional pre-loaded config to avoid repeated load_config() calls.

    Returns:
        Path to the skill directory.

    Raises:
        SkillNotFoundError: If skill does not exist in repository.
        ValidationError: If skill name contains path traversal attempts.
    """
    # Validate skill name to prevent path traversal and ensure format consistency
    validate_skill_name(name)

    # Load config to get skills_store
    if config is None:
        config = load_config()
    skills_base = config.skills_store.resolve()
    skill_dir = skills_base / "skills" / name

    # Verify the resolved path is still within the skills directory
    try:
        resolved_skill_dir = skill_dir.resolve()
    except OSError as e:
        raise ValidationError(f"Could not resolve skill path: {skill_dir}") from e
    if not resolved_skill_dir.is_relative_to(skills_base):
        raise ValidationError(f"Skill path escaped repository: {name}")
    if not skill_dir.exists():
        raise SkillNotFoundError(f"Skill '{name}' not found in repository")
    return skill_dir


def find_version_dir(skill_dir: Path, version: str | None = None) -> Path:
    """Find version directory for a skill.

    Args:
        skill_dir: Path to the skill directory.
        version: Specific version to find, or None for latest stable.

    Returns:
        Path to the version directory.

    Raises:
        VersionNotFoundError: If no suitable version is found.
    """
    if version:
        # Check current skill directory first
        requested_version_path = skill_dir / version
        if requested_version_path.exists():
            return requested_version_path

        # Check .bk directory for history versions
        bk_path = skill_dir.parent.parent / ".bk" / f"{skill_dir.name}@{version}"
        if bk_path.exists():
            return bk_path

        raise VersionNotFoundError(
            f"Version '{version}' not found for skill '{skill_dir.name}'"
        )

    if not skill_dir.exists():
        raise VersionNotFoundError(f"No version found for skill '{skill_dir.name}'")

    return skill_dir


# Using overloads to properly handle both Mapping and dataclass inputs
# - Mapping inputs are written directly
# - dataclass inputs are converted via dataclasses.asdict()


@overload
def atomic_write_toml(path: Path, data: Mapping[str, object]) -> None: ...


@overload
def atomic_write_toml(path: Path, data: object) -> None: ...


def atomic_write_toml(path: Path, data: Mapping[str, object] | object) -> None:
    """Atomically write a TOML file using a temporary file.

    Args:
        path: Target file path.
        data: Dictionary or dataclass to write as TOML.

    Raises:
        WriteError: If the write operation fails.
    """
    tmp_path: Path | None = None
    try:
        # Convert dataclass to dict if needed
        if is_dataclass(data) and not isinstance(data, type):
            # mypy doesn't narrow types through is_dataclass() check,
            # so we must use cast. This is safe because:
            # 1. is_dataclass() returns True for dataclass instances and classes
            # 2. isinstance(data, type) being False confirms it's an instance
            # 3. dataclasses.asdict() requires a dataclass instance
            dump_data: Mapping[str, object] = dataclasses.asdict(data)
        else:
            dump_data = cast("Mapping[str, object]", data)
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".toml", dir=path.parent, delete=False
        ) as tmp:
            tomli_w.dump(dump_data, tmp)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)
    except OSError as e:
        raise WriteError(f"Failed to write {path}") from e
    finally:
        # Clean up temp file if it still exists (replace may have failed).
        # Only ignore FileNotFoundError - other errors should be surfaced.
        if tmp_path is not None:
            with suppress(FileNotFoundError):
                tmp_path.unlink()


def resolve_skills_target_dir(
    *, global_flag: bool, project_path: Path | None = None
) -> Path:
    """Resolve the target directory for skill installation.

    Args:
        global_flag: If True, resolve to ~/.claude/skills/.
        project_path: Project path (required when global_flag is False).

    Returns:
        Resolved target skills directory path.

    Raises:
        ValidationError: If global_flag is False and project_path is None.
    """
    if global_flag:
        target = Path.home() / ".claude" / "skills"
    else:
        if project_path is None:
            raise ValidationError("project_path required for local installation")
        target = project_path / ".claude" / "skills"

    target.mkdir(parents=True, exist_ok=True)
    return target


def install_skill_copy(
    target_skills_dir: Path,
    name: str,
    skill_dir: Path,
    version_dir: Path,
) -> Path:
    """Copy a skill into the target directory (for fresh installs).

    Always uses directory copy. The target folder name is just {name},
    without any version suffix.

    Args:
        target_skills_dir: Path to the target skills directory.
        name: Skill name (used for target folder name).
        skill_dir: Path to the skill directory in the repo.
        version_dir: Path to the version directory to copy.

    Returns:
        Path to the created skill copy.

    Raises:
        LinkError: If copy operation fails.
    """
    project_skill_copy = target_skills_dir / name

    copy_skill_dir(version_dir, project_skill_copy, force=True)

    return project_skill_copy


def update_skill_copy(
    target_skills_dir: Path,
    name: str,
    skill_dir: Path,
    version_dir: Path,
) -> Path:
    """Update a skill with backup/restore protection.

    Creates a backup before updating. If the update fails, restores
    from backup. Backup is deleted on success.

    Args:
        target_skills_dir: Path to the target skills directory.
        name: Skill name.
        skill_dir: Path to the skill directory in the repo.
        version_dir: Path to the version directory to copy.

    Returns:
        Path to the updated skill copy.

    Raises:
        LinkError: If the update operation fails.
    """
    project_skill_path = target_skills_dir / name
    backup_path = target_skills_dir / f"{name}.bk"

    # Remove any stale backup from previous failed update
    if backup_path.exists():
        shutil.rmtree(backup_path)

    # Create backup of current installation if it exists
    if project_skill_path.exists():
        shutil.copytree(project_skill_path, backup_path)

    try:
        copy_skill_dir(version_dir, project_skill_path, force=True)
        # Success - delete backup
        if backup_path.exists():
            shutil.rmtree(backup_path)
        return project_skill_path
    except LinkError:
        # Failure - restore from backup
        if backup_path.exists():
            if project_skill_path.exists():
                shutil.rmtree(project_skill_path)
            shutil.move(str(backup_path), str(project_skill_path))
        raise
