"""Move skill from .dev to production."""

__all__ = ["mtp", "promote_skill"]

import click

from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.store import Promotion, SkillsStore


def promote_skill(name: str, *, config: SkillSyncConfig) -> Promotion:
    """Promote a dev skill to production with a versioned backup.

    Thin core over SkillsStore.promote: absorbs config loading so
    business tests inject a real config object instead of patching
    load_config.

    Args:
        name: Skill name.
        config: Pre-loaded repository config.

    Returns:
        Promotion describing the created production dir and backup.

    Raises:
        ValidationError: If the name is invalid.
        SkillNotFoundError: If .dev/{name} is missing or has no SKILL.md.
        WriteError: If the copy operations fail.
    """
    return SkillsStore(config.skills_store).promote(name)


@click.command()
@click.argument("name")
def mtp(name: str) -> None:
    """Move a skill from .dev to production.

    Copies the skill from .dev/{name} to the skills store root and
    creates a versioned backup in .bk/.
    """
    config = load_config()
    result = promote_skill(name, config=config)

    click.echo(f"Moved '{result.name}' to production (version: {result.version})")
    click.echo(f"  -> {result.target}")
    click.echo(f"  -> {result.backup}")
