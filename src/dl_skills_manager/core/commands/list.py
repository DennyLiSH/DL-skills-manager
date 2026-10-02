"""List skills command."""

__all__ = ["list_skills", "list_skills_cmd"]

from typing import TYPE_CHECKING

import click

from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.store import SkillsStore

if TYPE_CHECKING:
    from dl_skills_manager.core.types import SkillInfo


def list_skills(config: SkillSyncConfig) -> list[SkillInfo]:
    """List all skills in the repository.

    Args:
        config: Pre-loaded repository config.

    Returns:
        List of skill information objects.
    """
    return SkillsStore(config.skills_store).list_skills()


@click.command()
def list_skills_cmd() -> None:
    """List all available skills in the repository."""
    config = load_config()
    skills_path = config.skills_store

    skills = list_skills(config)

    if not skills:
        click.echo(f"No skills found in {skills_path}.")
        click.echo(
            "Please copy skill folders to this path, then run 'skill-sync list' again."
        )
        return

    click.echo(f"Skills in {skills_path}:")
    click.echo("")

    for skill in skills:
        if skill.history:
            version_label = f"(current, {len(skill.history)} history)"
        else:
            version_label = "(current)"
        click.echo(f"  {skill.name} {version_label}")
        if skill.history:
            click.echo(f"    history: {', '.join(skill.history)}")
