"""List versions command."""

__all__ = ["list_versions", "versions"]

import click

from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.store import SkillsStore


def list_versions(name: str, *, config: SkillSyncConfig) -> list[str]:
    """Version strings of a skill's backups, newest first.

    Validates that the skill exists in production first (single
    SkillsStore construction).

    Args:
        name: Skill name.
        config: Pre-loaded repository config.

    Returns:
        Backup version strings, newest first; empty when the skill
        has no history versions.

    Raises:
        SkillNotFoundError: If skill does not exist in repository.
        ValidationError: If skill name contains path traversal attempts.
    """
    store = SkillsStore(config.skills_store)
    store.find_skill(name)
    return store.list_backups(name)


@click.command()
@click.argument("name")
def versions(name: str) -> None:
    """List all versions of a skill."""
    config = load_config()
    history_versions = list_versions(name, config=config)

    click.echo(f"Versions of {name}:")
    click.echo("")
    click.echo("  current (latest)")

    for v in history_versions:
        click.echo(f"  {v}")

    if not history_versions:
        click.echo("  (no history versions)")
