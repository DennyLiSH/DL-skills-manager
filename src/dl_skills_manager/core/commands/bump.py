"""Bump (create new dev version) command."""

from __future__ import annotations

__all__ = ["bump"]

from datetime import date

import click

from dl_skills_manager.core.commands._shared import (
    atomic_write_toml,
    format_version_date,
    resolve_repo_path,
)
from dl_skills_manager.core.exceptions import SkillNotFoundError
from dl_skills_manager.core.manifest import read_skill_yaml


@click.command()
@click.argument("name")
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def bump(name: str, repo: str | None) -> None:
    """Create a new development version of a skill.

    Creates v{YYYY.MM.DD}-dev/ directory and updates skill.yaml.
    """
    # Determine repo path
    repo_path = resolve_repo_path(repo)

    # Find skill directory
    skill_dir = repo_path / "skills" / name
    if not skill_dir.exists():
        raise SkillNotFoundError(f"Skill '{name}' not found in repository")

    # Create new dev version with today's date
    today = date.today()
    version_str = format_version_date(today, dev=True)
    version_dir = skill_dir / version_str

    if version_dir.exists():
        click.echo(f"Version '{version_str}' already exists.")
        return

    version_dir.mkdir()

    # Create SKILL.md from template if exists
    skill_md = version_dir / "SKILL.md"
    template_path = repo_path / "templates" / "SKILL.md.tmpl"
    if template_path.exists():
        skill_md.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        # Read current SKILL.md from latest version as base
        current_md = None
        for v in sorted(skill_dir.iterdir(), reverse=True):
            if v.is_dir() and v.name.startswith("v"):
                md_path = v / "SKILL.md"
                if md_path.exists():
                    current_md = md_path.read_text(encoding="utf-8")
                    break
        skill_md.write_text(
            current_md or f"# {name}\n\nDevelopment version.\n", encoding="utf-8"
        )

    # Update skill.yaml
    skill_yaml_path = skill_dir / "skill.yaml"

    skill_data = read_skill_yaml(skill_dir)

    skill_data.version = version_str
    skill_data.updated = today.isoformat()

    # Atomic write using shared function
    atomic_write_toml(skill_yaml_path, skill_data)  # type: ignore[arg-type]

    click.echo(f"Created new dev version: {name}@{version_str}")
