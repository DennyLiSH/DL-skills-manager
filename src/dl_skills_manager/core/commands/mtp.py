"""Move skill from .dev to production."""

__all__ = ["mtp"]

import click

from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.store import SkillsStore, validate_skill_name


@click.command()
@click.argument("name")
def mtp(name: str) -> None:
    """Move a skill from .dev to production.

    Copies the skill from .dev/{name} to the skills store root and
    creates a versioned backup in .bk/.
    """
    validate_skill_name(name)

    config = load_config()
    result = SkillsStore(config.skills_store).promote(name)

    click.echo(f"Moved '{result.name}' to production (version: {result.version})")
    click.echo(f"  -> {result.target}")
    click.echo(f"  -> {result.backup}")
