"""Verify (promote dev to stable) command. TBD"""

__all__ = ["verify"]

import shutil
from dataclasses import replace
from datetime import date
from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    atomic_write_toml,
    find_skill_dir,
)
from dl_skills_manager.core.exceptions import (
    VersionNotFoundError,
    WriteError,
)
from dl_skills_manager.core.manifest import read_skill_yaml


@click.command()
@click.argument("name")
def verify(name: str) -> None:
    """Promote a development version to stable.

    Renames v{date}-dev/ to v{date}/ and updates skill.yaml stable_version.
    """
    # Find skill directory
    skill_dir = find_skill_dir(name)

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

    skill_data = read_skill_yaml(skill_dir)

    updated_data = replace(
        skill_data,
        stable_version=stable_name,
        version=stable_name,
        updated=today.isoformat(),
    )

    # Atomic write using shared function with rollback on failure
    try:
        atomic_write_toml(skill_yaml_path, updated_data)
    except WriteError:
        # Rollback: move stable back to dev
        shutil.move(stable_dir, dev_dir)
        raise

    click.echo(f"Promoted {name}@{dev_name} to stable {name}@{stable_name}")
