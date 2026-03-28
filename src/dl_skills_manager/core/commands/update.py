"""Update skill command."""

__all__ = ["update"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    update_skill_copy,
)
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")
@click.argument("project", default=".")
def update(name: str, project: str) -> None:
    """Update a skill to the latest stable version.

    Re-resolves the latest version from the repository and updates the symlink.
    """
    # Project path
    project_path = Path(project).resolve()

    # Find skill and version directories (update always uses stable/latest)
    config = load_config()
    skill_dir = find_skill_dir(name, config=config)
    version_dir = find_version_dir(skill_dir, version=None)

    # Check current installed version via symlink resolution
    project_skill_link = project_path / ".claude" / "skills" / name
    current_version: str | None = None
    if project_skill_link.is_symlink():
        resolved = project_skill_link.resolve()
        current_version = resolved.parent.name

    # Create symlink/copy
    update_skill_copy(
        project_path,
        name,
        skill_dir,
        version_dir,
    )

    click.echo(f"Updated {name} from {current_version or 'none'} to latest")
