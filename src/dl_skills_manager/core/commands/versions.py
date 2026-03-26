"""List versions command."""

__all__ = ["versions"]

import click

from dl_skills_manager.core.commands._shared import find_skill_dir


@click.command()
@click.argument("name")
def versions(name: str) -> None:
    """List all versions of a skill."""
    # Find skill directory
    skill_dir = find_skill_dir(name)

    # List all version directories
    version_dirs = [
        v for v in skill_dir.iterdir() if v.is_dir() and v.name.startswith("v")
    ]

    if not version_dirs:
        click.echo(f"No versions found for skill '{name}'")
        return

    click.echo(f"Versions of {name}:")
    click.echo("")

    for v_dir in sorted(version_dirs, reverse=True):
        click.echo(f"  {v_dir.name}")
