"""Remove skill command."""

__all__ = ["remove"]

from pathlib import Path

import click

from dl_skills_manager.core.linker import remove_link


@click.command()
@click.argument("name")
@click.argument("project", default=".")
def remove(name: str, project: str) -> None:
    """Remove an installed skill from the current project.

    Removes the symlink/copy.
    """
    project_path = Path(project).resolve()

    # Remove symlink/copy
    project_skill_path = project_path / ".claude" / "skills" / name

    # Check if skill is installed
    if not (project_skill_path.exists() or project_skill_path.is_symlink()):
        click.echo(f"Skill '{name}' is not installed in this project.")
        return

    # Remove the link
    remove_link(project_skill_path)

    click.echo(f"Removed {name} from project.")
