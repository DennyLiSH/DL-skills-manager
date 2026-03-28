"""List versions command."""

__all__ = ["versions"]

import click

from dl_skills_manager.core.commands._shared import find_skill_dir
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")
def versions(name: str) -> None:
    """List all versions of a skill."""
    config = load_config()
    find_skill_dir(name, config=config)  # validate skill exists

    bk_dir = config.skills_store / ".bk"

    # Collect history versions from .bk/
    history_versions: list[str] = []
    if bk_dir.exists():
        prefix = f"{name}@"
        for entry in bk_dir.iterdir():
            if entry.is_dir() and entry.name.startswith(prefix):
                version = entry.name[len(prefix) :]
                history_versions.append(version)

    click.echo(f"Versions of {name}:")
    click.echo("")
    click.echo("  current (latest)")

    for v in sorted(history_versions, reverse=True):
        click.echo(f"  {v}")

    if not history_versions:
        click.echo("  (no history versions)")
