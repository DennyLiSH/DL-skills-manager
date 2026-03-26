"""Install skill command."""

__all__ = ["install"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    install_skill_copy,
)
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")  # format: skill-name[@version]
@click.argument("project", default=".")
def install(name: str, project: str) -> None:
    """Install a skill into the current project.

    Creates a symlink (or copies) the skill to .claude/skills/{skill_name}.

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
    config = load_config()
    skills_store = config.skills_store

    # Determine version directory
    if version:
        version_dir = skills_store / ".bk" / f"{name}@{version}"
    else:
        version_dir = skills_store / name  # latest

    # Project path
    project_path = Path(project).resolve()

    # Create symlink/copy
    project_skill_link = install_skill_copy(
        project_path,
        name,
        skills_store,  # skill_dir (parent for lookup)
        version_dir,
    )

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {project_skill_link}")
