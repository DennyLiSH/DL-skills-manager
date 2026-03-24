"""Remove skill command."""

from __future__ import annotations

__all__ = ["remove"]

from pathlib import Path

import click

from dl_skills_manager.core.exceptions import LinkError
from dl_skills_manager.core.linker import remove_link
from dl_skills_manager.core.manifest import remove_skill_from_manifest


@click.command()
@click.argument("name")
@click.argument("project", default=".")
def remove(name: str, project: str) -> None:
    """Remove an installed skill from the current project.

    Removes the symlink/copy and updates the project's skills.toml.
    """
    project_path = Path(project).resolve()

    # Remove symlink/copy
    project_skill_path = project_path / ".claude" / "skills" / name

    # Only try to remove if the path exists
    if project_skill_path.exists() or project_skill_path.is_symlink():
        try:
            remove_link(project_skill_path)
        except LinkError:
            # Still update manifest even if link removal fails
            remove_skill_from_manifest(project_path, name)
            raise
    else:
        click.echo(f"Skill '{name}' is not installed in this project.")
        # Remove from manifest in case it's orphaned
        remove_skill_from_manifest(project_path, name)
        return

    # Remove from manifest (handles case where skill wasn't in manifest)
    remove_skill_from_manifest(project_path, name)

    click.echo(f"Removed {name} from project.")
