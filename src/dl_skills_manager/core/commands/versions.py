"""List versions command."""

__all__ = ["versions"]

import click

from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.store import SkillsStore


@click.command()
@click.argument("name")
def versions(name: str) -> None:
    """List all versions of a skill."""
    config = load_config()
    SkillsStore(config.skills_store).find_skill(name)  # validate skill exists

    history_versions = SkillsStore(config.skills_store).list_backups(name)

    click.echo(f"Versions of {name}:")
    click.echo("")
    click.echo("  current (latest)")

    for v in history_versions:
        click.echo(f"  {v}")

    if not history_versions:
        click.echo("  (no history versions)")
