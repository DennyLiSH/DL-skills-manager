"""Update skill command."""

from __future__ import annotations

__all__ = ["update"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    install_skill_link,
    resolve_repo_path,
)
from dl_skills_manager.core.manifest import read_project_manifest


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def update(name: str, project: str, repo: str | None) -> None:
    """Update a skill to the latest stable version.

    Reads the skill's skill.yaml to find the stable version and reinstalls.
    Only updates if a newer version is available.
    """
    # Determine repo path
    repo_path = resolve_repo_path(repo)

    # Project path
    project_path = Path(project).resolve()

    # Find skill and version directories (update always uses stable/latest)
    skill_dir = find_skill_dir(repo_path, name)
    version_dir = find_version_dir(skill_dir, version=None)
    actual_version = version_dir.name

    # Check current installed version and save for rollback
    manifest = read_project_manifest(project_path)
    skill_entry = manifest.skills.get(name)
    current_version = skill_entry.version if skill_entry else None
    current_source = skill_entry.source if skill_entry else None

    if current_version == actual_version:
        click.echo(f"{name} is already at the latest version ({actual_version})")
        return

    # Create symlink/copy and update manifest with rollback on failure
    install_skill_link(
        project_path,
        name,
        skill_dir,
        version_dir,
        manifest,
        current_source,
        current_version,
    )

    click.echo(f"Updated {name} from {current_version} to {actual_version}")
