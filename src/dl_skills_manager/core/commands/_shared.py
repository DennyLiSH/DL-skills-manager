"""Shared utilities for CLI commands.

Provides common functionality used across multiple commands such as
repository path resolution, skill directory lookup, and version parsing.
"""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import is_dataclass
from datetime import date
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml

import click
import tomli_w
from packaging.version import InvalidVersion, Version

from dl_skills_manager.core.config import get_default_repo_path, load_repo_config
from dl_skills_manager.core.exceptions import (
    ConfigError,
    SkillNotFoundError,
    VersionNotFoundError,
    WriteError,
)
from dl_skills_manager.core.linker import remove_link
from dl_skills_manager.core.manifest import (
    add_skill_to_manifest,
    read_project_manifest,
    write_project_manifest,
)

__all__ = [
    "atomic_write_toml",
    "find_skill_dir",
    "find_version_dir",
    "format_version_date",
    "resolve_repo_path",
    "rollback_manifest_update",
    "validate_skill_name",
]


def format_version_date(d: date, *, dev: bool = False) -> str:
    """Format a date as a version string.

    Args:
        d: Date to format.
        dev: If True, append '-dev' suffix.

    Returns:
        Version string in format 'vYYYY.MM.DD' or 'vYYYY.MM.DD-dev'.
    """
    version = f"v{d.strftime('%Y.%m.%d')}"
    if dev:
        version += "-dev"
    return version


def _parse_version(v: str) -> tuple[int, int]:
    """Parse version string for proper sorting.

    Args:
        v: Version string (e.g., "v2026.03.23", "v2026.03.23-dev").

    Returns:
        Tuple of (priority, dev_flag) for sorting.
        - priority: Higher = newer version (0 for invalid)
        - dev_flag: 0 for stable, 1 for dev (stable versions sort first)
        Invalid versions get priority 0 to sort to the bottom.
    """
    is_dev = v.endswith("-dev")
    clean = v.replace("-dev", "").lstrip("v")
    try:
        version = Version(clean)
        # Use base_version components to avoid pre-release suffixes
        parts = version.base_version.split(".")
        # Pad parts to at least 3 for consistent sorting
        padded = parts + ["0"] * (3 - len(parts))
        priority = int(padded[0]) * 10000 + int(padded[1]) * 100 + int(padded[2])
        return (priority, 1 if is_dev else 0)
    except InvalidVersion:
        return (0, 0)


def resolve_repo_path(repo: str | None) -> Path:
    """Resolve repository path from CLI option.

    Args:
        repo: CLI --repo option value.

    Returns:
        Resolved repository path.
    """
    repo_path = Path(repo).expanduser().resolve() if repo else get_default_repo_path()

    try:
        config = load_repo_config(repo_path)
        return config.path
    except ConfigError as e:
        click.echo(
            f"Warning: {repo_path} is not a valid repository config, using path as-is",
            err=True,
        )
        if not repo_path.exists():
            raise ConfigError(f"Repository path does not exist: {repo_path}") from e
        return repo_path


def validate_skill_name(name: str) -> None:
    """Validate skill name format.

    Args:
        name: Skill name to validate.

    Raises:
        ValueError: If skill name contains invalid characters or patterns.
    """
    # Check path traversal patterns first for proper error messages
    if ".." in name or name.startswith(("~", "/", "\\", "$")):
        raise ValueError(f"Invalid skill name: {name}")
    if not all(c.isalnum() or c in "-_" for c in name):
        raise ValueError("Skill name must be alphanumeric, hyphens, or underscores")


def find_skill_dir(repo_path: Path, name: str) -> Path:
    """Find skill directory in repository.

    Args:
        repo_path: Path to the repository.
        name: Skill name.

    Returns:
        Path to the skill directory.

    Raises:
        SkillNotFoundError: If skill does not exist in repository.
        ValueError: If skill name contains path traversal attempts.
    """
    # Validate skill name to prevent path traversal and ensure format consistency
    validate_skill_name(name)
    skill_dir = repo_path / "skills" / name
    # Verify the resolved path is still within the skills directory
    skills_base = (repo_path / "skills").resolve()
    resolved_skill_dir = skill_dir.resolve()
    if not resolved_skill_dir.is_relative_to(skills_base):
        raise ValueError(f"Skill path escaped repository: {name}")
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
        requested_version_path = skill_dir / version
        if not requested_version_path.exists():
            raise VersionNotFoundError(
                f"Version '{version}' not found for skill '{skill_dir.name}'"
            )
        return requested_version_path

    def find_stable_or_latest() -> Path | None:
        """Find stable version from skill.yaml or latest version directory."""
        skill_yaml_path = skill_dir / "skill.yaml"
        if skill_yaml_path.exists():
            try:
                with skill_yaml_path.open("rb") as f:
                    skill_data = load_toml(f)
                    stable = skill_data.get("stable_version", "")
                    if stable:
                        candidate: Path = skill_dir / stable
                        if candidate.exists():
                            return candidate
            except TOMLDecodeError:
                # Malformed skill.yaml, skip and fall back to version directory
                pass

        # Fall back to any version
        version_dirs = [
            d for d in skill_dir.iterdir() if d.is_dir() and d.name.startswith("v")
        ]
        for v in sorted(
            version_dirs,
            key=lambda p: _parse_version(p.name),
            reverse=True,
        ):
            return v
        return None

    version_path: Path | None = find_stable_or_latest()

    if version_path is None or not version_path.exists():
        raise VersionNotFoundError(f"No version found for skill '{skill_dir.name}'")

    return version_path


def atomic_write_toml(path: Path, data: Mapping[str, object]) -> None:
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
        dump_data = _dataclass_to_dict(data) if is_dataclass(data) else data
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".toml", dir=path.parent, delete=False
        ) as tmp:
            tomli_w.dump(dump_data, tmp)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
    except OSError as e:
        raise WriteError(f"Failed to write {path}") from e
    finally:
        # Clean up temp file if it still exists (replace failed)
        if tmp_path is not None and tmp_path.exists():
            with suppress(OSError):
                tmp_path.unlink()


def _dataclass_to_dict(data: object) -> dict[str, object]:
    """Convert a dataclass to a dictionary for TOML serialization.

    Args:
        data: A dataclass instance.

    Returns:
        A dictionary representation of the dataclass.
    """
    import dataclasses
    result: dict[str, object] = dataclasses.asdict(data)  # type: ignore[call-overload]
    return result


def rollback_manifest_update(
    project_path: Path,
    name: str,
    project_skill_link: Path,
    previous_source: str | None,
    previous_version: str | None,
) -> None:
    """Rollback a manifest update after a failed operation.

    Removes the created link and restores the previous installation state.

    Args:
        project_path: Path to the project.
        name: Skill name.
        project_skill_link: Path to the created link/directory.
        previous_source: Previous source path as string, or None.
        previous_version: Previous version string, or None.
    """
    remove_link(project_skill_link)
    if previous_source and previous_version:
        add_skill_to_manifest(
            project_path, name, Path(previous_source), previous_version
        )
    else:
        # No previous installation, remove from manifest entirely
        manifest = read_project_manifest(project_path)
        if name in manifest.skills:
            del manifest.skills[name]
            write_project_manifest(project_path, manifest)
