"""Update skill command."""

__all__ = ["update"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    resolve_skills_target_dir,
    update_skill_copy,
)
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option("--global", "is_global", is_flag=True, default=False,
              help="Update skill in ~/.claude/skills/ instead of a project.")
def update(name: str, project: str, is_global: bool) -> None:
    """Update a skill to the latest stable version.

    Re-resolves the latest version from the repository and updates the symlink.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Resolve target skills directory
    if is_global:
        target_skills_dir = resolve_skills_target_dir(global_flag=True)
    else:
        project_path = Path(project).resolve()
        target_skills_dir = resolve_skills_target_dir(
            global_flag=False, project_path=project_path,
        )

    # Find skill and version directories (update always uses stable/latest)
    config = load_config()
    skill_dir = find_skill_dir(name, config=config)
    version_dir = find_version_dir(skill_dir, version=None)

    # Check current installed version via symlink resolution
    project_skill_link = target_skills_dir / name
    current_version: str | None = None
    if project_skill_link.is_symlink():
        resolved = project_skill_link.resolve()
        current_version = resolved.parent.name

    # Create symlink/copy
    update_skill_copy(
        target_skills_dir,
        name,
        skill_dir,
        version_dir,
    )

    click.echo(f"Updated {name} from {current_version or 'none'} to latest")
