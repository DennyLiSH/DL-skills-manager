"""List versions command."""

from __future__ import annotations

__all__ = ["versions"]

from tomllib import load as load_toml

import click

from dl_skills_manager.core.commands._shared import resolve_repo_path
from dl_skills_manager.core.exceptions import SkillNotFoundError


@click.command()
@click.argument("name")
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def versions(name: str, repo: str | None) -> None:
    """List all versions of a skill."""
    # Determine repo path
    repo_path = resolve_repo_path(repo)

    # Find skill directory
    skill_dir = repo_path / "skills" / name
    if not skill_dir.exists():
        raise SkillNotFoundError(f"Skill '{name}' not found in repository")

    # Read skill.yaml for stable version info
    skill_yaml_path = skill_dir / "skill.yaml"
    stable_version = ""
    current_version = ""

    if skill_yaml_path.exists():
        with skill_yaml_path.open("rb") as f:
            data = load_toml(f)
            stable_version = data.get("stable_version", "")
            current_version = data.get("version", "")

    # List all versions
    version_dirs = [
        v for v in skill_dir.iterdir() if v.is_dir() and v.name.startswith("v")
    ]

    if not version_dirs:
        click.echo(f"No versions found for skill '{name}'")
        return

    click.echo(f"Versions of {name}:")
    click.echo("")

    for v_dir in sorted(version_dirs, reverse=True):
        version_name = v_dir.name
        markers: list[str] = []

        if version_name == stable_version:
            markers.append("stable")
        if version_name == current_version:
            markers.append("current")

        marker_str = f" ({', '.join(markers)})" if markers else ""
        click.echo(f"  {version_name}{marker_str}")
