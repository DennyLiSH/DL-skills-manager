"""Install skill command."""

__all__ = ["install"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    install_skill_copy,
    resolve_skills_target_dir,
    validate_skill_name,
)
from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.linker import create_link


@click.command()
@click.argument("name")  # format: skill-name[@version]
@click.argument("project", default=".")
@click.option("--global", "is_global", is_flag=True, default=False,
              help="Install to ~/.claude/skills/ instead of a project.")
@click.option(
    "--link-mode",
    type=click.Choice(["symlink", "copy"]),
    default=None,
    help="Override default link mode (symlink or copy) for this installation.",
)
def install(name: str, project: str, is_global: bool, link_mode: str | None) -> None:
    """Install a skill into the current project.

    Creates a symlink or copies the skill to .claude/skills/{skill_name},
    depending on config or --link-mode override.

    Supports name@version syntax for specifying version directly in the name.

    Args:
        name: Name of the skill to install (optionally with @version suffix).
        project: Path to the project directory (default: current directory).
        is_global: If True, install to ~/.claude/skills/ globally.
        link_mode: Override the default link mode from config.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Parse name@version syntax
    version: str | None = None
    if "@" in name:
        name, version = name.rsplit("@", 1)

    validate_skill_name(name)

    # Load config and determine effective link mode
    config = load_config()
    effective_mode = link_mode or config.default_link_mode

    # Find skill and version directories with validation
    skill_dir = find_skill_dir(name, config=config)
    version_dir = find_version_dir(skill_dir, version=version)

    # Resolve target skills directory
    if is_global:
        target_skills_dir = resolve_skills_target_dir(global_flag=True)
    else:
        project_path = Path(project).resolve()
        target_skills_dir = resolve_skills_target_dir(
            global_flag=False, project_path=project_path,
        )

    # Create symlink or copy based on effective mode
    project_skill_path = target_skills_dir / name

    if effective_mode == "symlink":
        create_link(version_dir, project_skill_path, force=True)
    else:
        install_skill_copy(
            target_skills_dir,
            name,
            skill_dir,
            version_dir,
        )

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {project_skill_path}")
