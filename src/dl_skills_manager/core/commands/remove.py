"""Remove skill command."""

__all__ = ["remove"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    resolve_skills_target_dir,
    validate_skill_name,
)
from dl_skills_manager.core.linker import remove_link


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option("--global", "is_global", is_flag=True, default=False,
              help="Remove skill from ~/.claude/skills/ instead of a project.")
def remove(name: str, project: str, is_global: bool) -> None:
    """Remove an installed skill from the current project.

    Removes the symlink/copy.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    validate_skill_name(name)

    # Resolve target skills directory
    if is_global:
        target_skills_dir = resolve_skills_target_dir(global_flag=True)
    else:
        project_path = Path(project).resolve()
        target_skills_dir = resolve_skills_target_dir(
            global_flag=False, project_path=project_path,
        )

    # Remove symlink/copy
    project_skill_path = target_skills_dir / name

    # Check if skill is installed
    if not (project_skill_path.exists() or project_skill_path.is_symlink()):
        scope = "global skills" if is_global else "this project"
        click.echo(f"Skill '{name}' is not installed in {scope}.")
        return

    # Remove the link
    remove_link(project_skill_path)

    scope = "global skills" if is_global else "project"
    click.echo(f"Removed {name} from {scope}.")
