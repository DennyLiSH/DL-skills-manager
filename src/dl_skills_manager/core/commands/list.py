"""List skills command."""

__all__ = ["list_skills", "list_skills_cmd"]

from pathlib import Path

import click

from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.types import SkillInfo


def list_skills() -> tuple[list[SkillInfo], list[str]]:
    """List all skills in the repository.

    Returns:
        Tuple of (skills list, warnings list).
    """
    config = load_config()
    skills_dir = config.skills_store
    if not skills_dir.exists():
        return [], []

    skills: list[SkillInfo] = []
    warnings: list[str] = []

    bk_dir = skills_dir / ".bk"
    history_map: dict[str, list[str]] = {}

    # Scan .bk for history versions first
    if bk_dir.exists():
        for bk_item in sorted(bk_dir.iterdir()):
            if not bk_item.is_dir():
                continue
            # Format: {skill-name}@{version}
            if "@" in bk_item.name:
                skill_name, version = bk_item.name.split("@", 1)
                if skill_name not in history_map:
                    history_map[skill_name] = []
                history_map[skill_name].append(version)

    # Scan skills_store for valid skills
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        # Skip .bk directory itself
        if skill_dir.name == ".bk":
            continue

        # Only directories containing SKILL.md are considered skills
        if not (skill_dir / "SKILL.md").exists():
            continue

        skill_name = skill_dir.name

        # Get history from .bk
        history = sorted(history_map.get(skill_name, []), reverse=True)

        skills.append(
            SkillInfo(
                name=skill_name,
                description="",
                version="current",
                history=tuple(history),
            )
        )

    return skills, warnings


@click.command()
def list_skills_cmd() -> None:
    """List all available skills in the repository."""
    config = load_config()
    skills_path = config.skills_store

    skills, warnings = list_skills()

    for warning in warnings:
        click.echo(f"Warning: {warning}", err=True)

    if not skills:
        click.echo(f"No skills found in {skills_path}.")
        click.echo("Please copy skill folders to this path, then run 'skill-sync list' again.")
        return

    click.echo(f"Skills in {skills_path}:")
    click.echo("")

    for skill in skills:
        if skill.history:
            version_label = f"(current, {len(skill.history)} history)"
        else:
            version_label = "(current)"
        click.echo(f"  {skill.name} {version_label}")
        if skill.description:
            click.echo(f"    {skill.description}")
        if skill.history:
            click.echo(f"    history: {', '.join(skill.history)}")
