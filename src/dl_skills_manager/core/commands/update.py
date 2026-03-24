"""Update skill command."""

from __future__ import annotations

__all__ = ["update"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    resolve_repo_path,
)
from dl_skills_manager.core.exceptions import LinkError, ManifestError
from dl_skills_manager.core.linker import create_link, remove_link
from dl_skills_manager.core.manifest import add_skill_to_manifest, read_project_manifest


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
    skill_entry = manifest["skills"].get(name)
    current_version = skill_entry.get("version") if skill_entry else None
    current_source = skill_entry.get("source") if skill_entry else None

    if current_version == actual_version:
        click.echo(f"{name} is already at the latest version ({actual_version})")
        return

    # Create symlink/copy in project
    project_skill_link = project_path / ".claude" / "skills" / name

    create_link(version_dir, project_skill_link, force=True)

    # Update manifest with rollback on failure
    try:
        add_skill_to_manifest(project_path, name, skill_dir, actual_version)
    except (ManifestError, OSError, LinkError):
        # Rollback: remove the link we just created
        remove_link(project_skill_link)
        # Restore previous installation if one existed
        if current_source and current_version:
            add_skill_to_manifest(
                project_path, name, Path(current_source), current_version
            )
        raise

    click.echo(f"Updated {name} from {current_version} to {actual_version}")
