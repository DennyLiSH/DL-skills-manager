"""Project status command."""

__all__ = ["status"]

from pathlib import Path

import click

from dl_skills_manager.core.manifest import get_installed_skills


@click.command()
@click.argument("project", default=".")
def status(project: str) -> None:
    """Show installed skills in the current project.

    Reads the project's skills.toml and displays installed skills.
    """
    project_path = Path(project).resolve()

    skills = get_installed_skills(project_path)

    if not skills:
        click.echo(f"No skills installed in {project_path}")
        return

    click.echo(f"Installed skills in {project_path}:")
    click.echo("")

    for skill in skills:
        click.echo(f"  {skill.name}@{skill.version}")
        click.echo(f"    Source: {skill.source}")
