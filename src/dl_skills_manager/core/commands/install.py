"""Install skill command."""

__all__ = ["install"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    install_skill_copy,
    resolve_skills_target_dir,
    validate_skill_name,
)
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")  # format: skill-name[@version]
@click.argument("project", default=".")
@click.option("--global", "is_global", is_flag=True, default=False,
              help="Install to ~/.claude/skills/ instead of a project.")
def install(name: str, project: str, is_global: bool) -> None:
    """Install a skill into the current project.

    Creates a symlink (or copies) the skill to .claude/skills/{skill_name}.

    Supports name@version syntax for specifying version directly in the name.

    Args:
        name: Name of the skill to install (optionally with @version suffix).
        project: Path to the project directory (default: current directory).
        is_global: If True, install to ~/.claude/skills/ globally.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Parse name@version syntax
    version: str | None = None
    if "@" in name:
        name, version = name.rsplit("@", 1)

    validate_skill_name(name)

    # Load config and determine paths
    config = load_config()
    skills_store = config.skills_store

    # Determine version directory
    if version:
        version_dir = skills_store / ".bk" / f"{name}@{version}"
    else:
        version_dir = skills_store / "skills" / name  # latest

    # Resolve target skills directory
    if is_global:
        target_skills_dir = resolve_skills_target_dir(global_flag=True)
    else:
        project_path = Path(project).resolve()
        target_skills_dir = resolve_skills_target_dir(
            global_flag=False, project_path=project_path,
        )

    # Create symlink/copy
    project_skill_link = install_skill_copy(
        target_skills_dir,
        name,
        skills_store,  # skill_dir (parent for lookup)
        version_dir,
    )

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {project_skill_link}")
