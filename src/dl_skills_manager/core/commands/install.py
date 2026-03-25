"""Install skill command."""

__all__ = ["install"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    install_skill_link,
)
from dl_skills_manager.core.config import load_repo_config
from dl_skills_manager.core.manifest import read_project_manifest


@click.command()
@click.argument("name")  # format: skill-name[@version]
@click.argument("project", default=".")
def install(name: str, project: str) -> None:
    """Install a skill into the current project.

    Creates a symlink (or copies) the skill to .claude/skills/{skill_name}.
    Updates the project's skills.toml manifest.

    Supports name@version syntax for specifying version directly in the name.

    Args:
        name: Name of the skill to install (optionally with @version suffix).
        project: Path to the project directory (default: current directory).
    """
    # Parse name@version syntax
    version: str | None = None
    if "@" in name:
        name_parts = name.rsplit("@", 1)
        name = name_parts[0]
        version = name_parts[1] if len(name_parts) > 1 else None

    # Load config and determine paths
    config = load_repo_config()
    skills_store = config.skills_store

    # Determine version directory
    if version:
        version_dir = skills_store / ".bk" / f"{name}@{version}"
    else:
        version_dir = skills_store / name  # latest

    # Project path
    project_path = Path(project).resolve()

    # Check if skill was already installed to support proper rollback
    manifest = read_project_manifest(project_path)
    previous_entry = manifest.skills.get(name)
    previous_source = previous_entry.source if previous_entry else None
    previous_version = previous_entry.version if previous_entry else None

    # Create symlink/copy and update manifest with rollback on failure
    project_skill_link = install_skill_link(
        project_path,
        name,
        skills_store,  # skill_dir (parent for lookup)
        version_dir,
        manifest,
        previous_source,
        previous_version,
    )

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {project_skill_link}")
