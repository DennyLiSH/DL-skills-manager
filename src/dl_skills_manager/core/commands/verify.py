"""Verify (promote dev to stable) command."""

from __future__ import annotations

__all__ = ["verify"]

import shutil
from datetime import date
from pathlib import Path
from tomllib import load as load_toml

import click

from dl_skills_manager.core.commands._shared import atomic_write_toml, resolve_repo_path
from dl_skills_manager.core.exceptions import (
    SkillNotFoundError,
    VersionNotFoundError,
)
from dl_skills_manager.core.types import SkillYamlData


@click.command()
@click.argument("name")
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def verify(name: str, repo: str | None) -> None:
    """Promote a development version to stable.

    Renames v{date}-dev/ to v{date}/ and updates skill.yaml stable_version.
    """
    # Determine repo path
    repo_path = resolve_repo_path(repo)

    # Find skill directory
    skill_dir = repo_path / "skills" / name
    if not skill_dir.exists():
        raise SkillNotFoundError(f"Skill '{name}' not found in repository")

    # Find dev version
    dev_dir: Path | None = None
    for v in sorted(skill_dir.iterdir(), reverse=True):
        if v.is_dir() and v.name.endswith("-dev"):
            dev_dir = v
            break

    if not dev_dir:
        raise VersionNotFoundError(f"No dev version found for skill '{name}'")

    # Get version string without -dev suffix
    dev_name = dev_dir.name
    stable_name = dev_name.replace("-dev", "")

    # Check if stable version already exists
    stable_dir = skill_dir / stable_name
    if stable_dir.exists():
        raise VersionNotFoundError(f"Stable version '{stable_name}' already exists")

    # Rename dev to stable (shutil.move works across volumes)
    shutil.move(dev_dir, stable_dir)

    # Update skill.yaml
    today = date.today()
    skill_yaml_path = skill_dir / "skill.yaml"

    skill_data: SkillYamlData
    if skill_yaml_path.exists():
        with skill_yaml_path.open("rb") as f:
            skill_data = load_toml(f)  # type: ignore[assignment]
    else:
        skill_data = SkillYamlData()

    skill_data["stable_version"] = stable_name
    skill_data["version"] = stable_name
    skill_data["updated"] = today.isoformat()

    # Atomic write using shared function
    atomic_write_toml(skill_yaml_path, skill_data)

    click.echo(f"Promoted {name}@{dev_name} to stable {name}@{stable_name}")
