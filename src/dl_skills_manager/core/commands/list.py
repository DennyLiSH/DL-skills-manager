"""List skills command."""

from __future__ import annotations

__all__ = ["list_cmd", "list_skills"]

from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml

import click

from dl_skills_manager.core.commands._shared import resolve_repo_path
from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.types import SkillInfo


def list_skills(
    repo_path: Path | None = None,
) -> tuple[list[SkillInfo], list[str]]:
    """List all skills in the repository.

    Args:
        repo_path: Path to the repository. Defaults to ~/.skills-repo.

    Returns:
        Tuple of (skills list, warnings list).
    """
    if repo_path is None:
        repo_path = get_default_repo_path()

    skills_dir = repo_path / "skills"
    if not skills_dir.exists():
        return [], []

    skills: list[SkillInfo] = []
    warnings: list[str] = []

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        # Skip hidden directories and non-alphanumeric skill names
        if skill_dir.name.startswith("."):
            continue

        skill_name = skill_dir.name

        # Count versions
        version_count = sum(
            1 for v in skill_dir.iterdir() if v.is_dir() and v.name.startswith("v")
        )

        # Read skill.yaml for description
        skill_yaml = skill_dir / "skill.yaml"
        description = ""
        if skill_yaml.exists():
            try:
                with skill_yaml.open("rb") as f:
                    data = load_toml(f)
                    description = data.get("description", "")
            except TOMLDecodeError:
                warnings.append(f"Skipping malformed {skill_yaml}")

        skills.append(
            SkillInfo(
                name=skill_name,
                description=description,
                versions=version_count,
            )
        )

    return skills, warnings


@click.command()
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-base)",
)
def list_cmd(repo: str | None) -> None:
    """List all available skills in the repository."""
    repo_path = resolve_repo_path(repo)

    skills, warnings = list_skills(repo_path)

    for warning in warnings:
        click.echo(f"Warning: {warning}", err=True)

    if not skills:
        click.echo("No skills found. Run 'dl-skills-manager init' first.")
        return

    click.echo(f"Skills in {repo_path}:")
    click.echo("")

    for skill in skills:
        version_count = skill.versions
        version_label = f"({version_count} version{'s' if version_count != 1 else ''})"
        click.echo(f"  {skill.name} {version_label}")
        if skill.description:
            click.echo(f"    {skill.description}")
