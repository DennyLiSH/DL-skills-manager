"""Install skill command."""

from __future__ import annotations

__all__ = ["install"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    resolve_repo_path,
    rollback_manifest_update,
)
from dl_skills_manager.core.exceptions import LinkError, ManifestError
from dl_skills_manager.core.linker import create_link
from dl_skills_manager.core.manifest import add_skill_to_manifest, read_project_manifest


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option(
    "--version",
    default=None,
    help="Version to install (default: latest stable)",
)
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def install(name: str, project: str, version: str | None, repo: str | None) -> None:
    """Install a skill into the current project.

    Creates a symlink (or copies) the skill to .claude/skills/{skill_name}.
    Updates the project's skills.toml manifest.

    Args:
        name: Name of the skill to install.
        project: Path to the project directory (default: current directory).
        version: Specific version to install (default: latest stable).
        repo: Path to skills repository (default: ~/.skills-repo).
    """
    # Determine repo path
    repo_path = resolve_repo_path(repo)

    # Project path
    project_path = Path(project).resolve()

    # Find skill and version directories
    skill_dir = find_skill_dir(repo_path, name)
    version_dir = find_version_dir(skill_dir, version)
    actual_version = version_dir.name

    # Create symlink/copy in project
    project_skill_link = project_path / ".claude" / "skills" / name

    # Check if skill was already installed to support proper rollback
    manifest = read_project_manifest(project_path)
    previous_entry = manifest.skills.get(name)
    previous_source = previous_entry.source if previous_entry else None
    previous_version = previous_entry.version if previous_entry else None

    create_link(version_dir, project_skill_link, force=True)

    # Update manifest with rollback on failure
    try:
        add_skill_to_manifest(project_path, name, skill_dir, actual_version)
    except (ManifestError, LinkError):
        rollback_manifest_update(
            project_path, name, project_skill_link, previous_source, previous_version
        )
        raise

    click.echo(f"Installed {name}@{actual_version} to {project_skill_link}")
