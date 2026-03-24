"""Install skill command."""

from __future__ import annotations

__all__ = ["install"]

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

    # Check if skill was already installed to support proper rollback
    manifest = read_project_manifest(project_path)
    previous_entry = manifest.skills.get(name)
    previous_source = previous_entry.source if previous_entry else None
    previous_version = previous_entry.version if previous_entry else None

    # Create symlink/copy and update manifest with rollback on failure
    install_skill_link(
        project_path, name, skill_dir, version_dir, previous_source, previous_version
    )

    project_skill_link = project_path / ".claude" / "skills" / name
    click.echo(f"Installed {name}@{actual_version} to {project_skill_link}")
