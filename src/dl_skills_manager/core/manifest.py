"""Project skills manifest management.

Handles reading and writing the project's skills.toml manifest file
which tracks installed skills and their sources.
"""

from __future__ import annotations

__all__ = [
    "add_skill_to_manifest",
    "ensure_project_manifest_dir",
    "get_installed_skills",
    "get_project_manifest_path",
    "read_project_manifest",
    "read_skill_yaml",
    "remove_skill_from_manifest",
    "write_project_manifest",
]

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager, suppress
from dataclasses import is_dataclass
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml
from typing import IO, Any

import tomli_w

from dl_skills_manager.core.exceptions import ManifestError
from dl_skills_manager.core.types import (
    InstalledSkill,
    ProjectManifest,
    SkillEntry,
    SkillYamlData,
)

PROJECT_MANIFEST_DIR = ".claude/skills"
PROJECT_MANIFEST_FILE = "skills.toml"

logger = logging.getLogger(__name__)


def _validate_project_dir(project_dir: Path) -> Path:
    """Validate project directory exists and is a directory.

    Args:
        project_dir: Path to the project.

    Returns:
        Resolved project directory path.

    Raises:
        ValueError: If project_dir is not a valid directory.
    """
    resolved = project_dir.resolve()
    if not resolved.exists():
        raise ValueError(f"Project directory does not exist: {project_dir}")
    if not resolved.is_dir():
        raise ValueError(f"Project path is not a directory: {project_dir}")
    return resolved


def _lock_file_windows(
    lock_path: Path, path: Path, mode: str
) -> Generator[tuple[IO[Any], Path]]:
    """Acquire exclusive lock on Windows using msvcrt.

    Args:
        lock_path: Path to the lock file.
        path: Path to the file to open.
        mode: File mode ('r' or 'rb' for reading, 'w' or 'wb' for writing).

    Yields:
        A tuple of (file object, lock file path).

    Raises:
        ManifestError: If lock cannot be acquired after retries.
    """
    import msvcrt
    import time

    with open(lock_path, "wb+") as _lock_file:
        for _attempt in range(100):
            try:
                msvcrt.locking(_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(0.01)
        else:
            msg = f"Could not acquire lock on {lock_path}"
            raise ManifestError(msg)

        try:
            with path.open(mode) as f:
                yield f, lock_path
        finally:
            msvcrt.locking(_lock_file.fileno(), msvcrt.LK_UNLCK, 1)


def _lock_file_unix(
    lock_path: Path, path: Path, mode: str
) -> Generator[tuple[IO[Any], Path]]:
    """Acquire exclusive lock on Unix using fcntl.

    Args:
        lock_path: Path to the lock file.
        path: Path to the file to open.
        mode: File mode ('r' or 'rb' for reading, 'w' or 'wb' for writing).

    Yields:
        A tuple of (file object, lock file path).
    """
    import fcntl

    with open(lock_path, "w") as _lock_file:
        fcntl.flock(_lock_file.fileno(), fcntl.LOCK_EX)  # type: ignore[attr-defined]
        try:
            with path.open(mode) as f:
                yield f, lock_path
        finally:
            fcntl.flock(_lock_file.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


@contextmanager
def _locked_file(path: Path, mode: str) -> Generator[tuple[IO[Any], Path]]:
    """Context manager for file locking during read/write operations.

    Uses fcntl on Unix and msvcrt on Windows for cross-platform support.
    Lock files are cleaned up after the context exits.

    Args:
        path: Path to the file to lock.
        mode: File mode ('r' or 'rb' for reading, 'w' or 'wb' for writing).

    Yields:
        A tuple of (file object, lock file path).

    Raises:
        ManifestError: If lock cannot be acquired after retries.
    """
    lock_path = path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        locker = _lock_file_windows
    else:
        locker = _lock_file_unix

    try:
        yield from locker(lock_path, path, mode)
    finally:
        with suppress(OSError):
            lock_path.unlink()


def get_project_manifest_path(project_dir: Path) -> Path:
    """Get the path to the project's skills.toml.

    Args:
        project_dir: Path to the project.

    Returns:
        Path to the manifest file.

    Raises:
        ValueError: If project_dir is not a valid directory.
    """
    _validate_project_dir(project_dir)
    return project_dir / PROJECT_MANIFEST_DIR / PROJECT_MANIFEST_FILE


def ensure_project_manifest_dir(project_dir: Path) -> Path:
    """Ensure the project manifest directory exists.

    Args:
        project_dir: Path to the project.

    Returns:
        Path to the manifest directory.

    Raises:
        ValueError: If project_dir is not a valid directory.
    """
    _validate_project_dir(project_dir)
    manifest_dir = project_dir / PROJECT_MANIFEST_DIR
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir


def read_project_manifest(project_dir: Path) -> ProjectManifest:
    """Read the project's skills.toml manifest.

    Args:
        project_dir: Path to the project.

    Returns:
        Project manifest structure.

    Raises:
        ManifestError: If the manifest cannot be read or parsed.
    """
    manifest_path = get_project_manifest_path(project_dir)

    if not manifest_path.exists():
        return ProjectManifest(skills={})

    try:
        with _locked_file(manifest_path, "rb") as (f, _lock_path):
            data = load_toml(f)
    except TOMLDecodeError as e:
        raise ManifestError(f"Failed to parse {manifest_path}: {e}") from e

    skills: dict[str, SkillEntry] = {}
    for name, entry in data.get("skills", {}).items():
        if isinstance(entry, dict):
            skills[name] = SkillEntry(
                source=entry.get("source", ""),
                version=entry.get("version", ""),
            )
    return ProjectManifest(skills=skills)


def write_project_manifest(
    project_dir: Path, manifest: ProjectManifest | dict[str, Any]
) -> None:
    """Write the project's skills.toml manifest.

    Args:
        project_dir: Path to the project.
        manifest: Manifest data to write (ProjectManifest dataclass or dict).

    Raises:
        ManifestError: If the manifest cannot be written.
    """
    # Ensure directory exists (validates project_dir)
    ensure_project_manifest_dir(project_dir)
    # Compute manifest path directly (no need to re-validate)
    manifest_path = project_dir / PROJECT_MANIFEST_DIR / PROJECT_MANIFEST_FILE

    try:
        with _locked_file(manifest_path, "wb") as (f, _lock_path):
            if is_dataclass(manifest):
                skills_dict = {
                    name: {"source": e.source, "version": e.version}
                    for name, e in manifest.skills.items()
                }
            else:
                skills_dict = dict(manifest.get("skills", {}).items())
            tomli_w.dump({"skills": skills_dict}, f)
    except OSError as e:
        raise ManifestError(f"Failed to write manifest: {e}") from e


def get_installed_skills(project_dir: Path) -> list[InstalledSkill]:
    """Get list of installed skills in a project.

    Args:
        project_dir: Path to the project.

    Returns:
        List of InstalledSkill objects.
    """
    manifest = read_project_manifest(project_dir)
    skills: list[InstalledSkill] = []

    for name, data in manifest.skills.items():
        source_str = data.source
        if not source_str:
            logger.warning(
                "Skipping entry with empty source for skill '%s' in manifest", name
            )
            continue
        skills.append(
            InstalledSkill(
                name=name,
                source=source_str,
                version=data.version,
            )
        )

    return skills


def add_skill_to_manifest(
    project_dir: Path,
    skill_name: str,
    source: Path,
    version: str,
) -> None:
    """Add a skill to the project manifest.

    Args:
        project_dir: Path to the project.
        skill_name: Name of the skill.
        source: Source path in the repository.
        version: Version being installed.
    """
    manifest = read_project_manifest(project_dir)
    manifest.skills[skill_name] = SkillEntry(
        source=str(source),
        version=version,
    )
    write_project_manifest(project_dir, manifest)


def remove_skill_from_manifest(project_dir: Path, skill_name: str) -> None:
    """Remove a skill from the project manifest.

    Args:
        project_dir: Path to the project.
        skill_name: Name of the skill to remove.
    """
    manifest = read_project_manifest(project_dir)
    if skill_name in manifest.skills:
        del manifest.skills[skill_name]
        write_project_manifest(project_dir, manifest)


def read_skill_yaml(skill_dir: Path) -> SkillYamlData:
    """Read skill.yaml from a skill directory.

    Args:
        skill_dir: Path to the skill directory (contains skill.yaml).

    Returns:
        SkillYamlData parsed from skill.yaml, or empty SkillYamlData if not found.
    """
    skill_yaml_path = skill_dir / "skill.yaml"
    if not skill_yaml_path.exists():
        return SkillYamlData()

    try:
        with skill_yaml_path.open("rb") as f:
            data = load_toml(f)
            return SkillYamlData(
                name=data.get("name", ""),
                description=data.get("description", ""),
                version=data.get("version", ""),
                stable_version=data.get("stable_version", ""),
                author=data.get("author", ""),
                tags=data.get("tags", []),
                created=data.get("created", ""),
                updated=data.get("updated", ""),
            )
    except TOMLDecodeError as e:
        raise ManifestError(f"Failed to parse {skill_yaml_path}: {e}") from e
