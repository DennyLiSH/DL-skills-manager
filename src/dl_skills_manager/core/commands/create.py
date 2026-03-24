"""Create new skill command."""

from __future__ import annotations

__all__ = ["create"]

from datetime import date

import click
import tomli_w

from dl_skills_manager.core.commands._shared import (
    format_version_date,
    resolve_repo_path,
)
from dl_skills_manager.core.exceptions import (
    RepoNotInitializedError,
    SkillAlreadyExistsError,
    ValidationError,
)


@click.command()
@click.argument("name")
@click.option(
    "--description",
    default="",
    help="Skill description",
)
@click.option(
    "--repo",
    type=click.Path(),
    default=None,
    help="Path to skills repository (default: ~/.skills-repo)",
)
def create(name: str, description: str, repo: str | None) -> None:
    """Create a new skill with initial version.

    Creates the skill directory structure:
    - skills/{name}/skill.yaml
    - skills/{name}/v{date}/
    - skills/{name}/v{date}/SKILL.md

    Args:
        name: Name of the skill to create.
        description: Description of the skill.
        repo: Path to skills repository (default: ~/.skills-repo).
    """
    # Validate skill name
    if not name or not name.strip():
        raise ValidationError("Skill name cannot be empty")
    if (
        ".." in name
        or name.startswith("/")
        or name.startswith("\\")
        or name.startswith("~")
    ):
        raise ValidationError(f"Invalid skill name: {name}")
    if "$" in name:
        raise ValidationError(f"Invalid skill name: {name}")
    if not all(c.isalnum() or c in "-_" for c in name):
        raise ValidationError(
            "Skill name must be alphanumeric, hyphens, or underscores"
        )

    # Determine repo path
    repo_path = resolve_repo_path(repo)

    skills_dir = repo_path / "skills"
    if not skills_dir.exists():
        raise RepoNotInitializedError(
            f"Repository not initialized at {repo_path}. "
            "Run 'dl-skills-manager init' first."
        )

    skill_dir = skills_dir / name
    if skill_dir.exists():
        raise SkillAlreadyExistsError(f"Skill '{name}' already exists in repository.")

    # Create skill directory
    skill_dir.mkdir(parents=True)

    # Create initial version directory with today's date
    today = date.today()
    version_str = format_version_date(today)
    version_dir = skill_dir / version_str
    version_dir.mkdir(parents=True)

    # Create skill.yaml
    skill_yaml = skill_dir / "skill.yaml"
    skill_data = {
        "name": name,
        "description": description,
        "version": version_str,
        "stable_version": "",
        "author": "",
        "tags": [],
        "created": today.isoformat(),
        "updated": today.isoformat(),
    }

    with skill_yaml.open("wb") as f:
        tomli_w.dump(skill_data, f)

    # Create SKILL.md from template if exists, otherwise create default
    skill_md = version_dir / "SKILL.md"
    template_path = repo_path / "templates" / "SKILL.md.tmpl"
    if template_path.exists():
        skill_md.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        skill_md.write_text(f"# {name}\n\n{description}\n", encoding="utf-8")

    click.echo(f"Created skill '{name}' at {skill_dir}")
    click.echo(f"  Initial version: {version_str}")
