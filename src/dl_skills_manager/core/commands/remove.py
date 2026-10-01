"""Remove skill command."""

__all__ = ["remove"]

import click

from dl_skills_manager.core.commands._shared import (
    resolve_command_target_dir,
    validate_skill_name,
)
from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.linker import remove_link


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    default=False,
    help="Remove skill from ~/.claude/skills/ instead of a project.",
)
@click.option(
    "--agent",
    default="claude",
    show_default=True,
    help="Target agent dir (claude/codex/pi/zcode/workbuddy or [agents]).",
)
def remove(name: str, project: str, *, is_global: bool, agent: str) -> None:
    """Remove an installed skill from a project or agent skills directory.

    Removes the symlink/copy. Use --global to target the agent's global
    skills dir instead of a project; use --agent to target another
    agent's skills dir (builtin registry or [agents] config overrides).

    Requires an initialized skill-sync repository: remove reads
    config.toml for [agents] overrides and fails when it is missing.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    validate_skill_name(name)

    # Load config: [agents] overrides affect target dir resolution (D6b)
    config = load_config()

    # Resolve target skills directory
    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )

    # Remove symlink/copy
    project_skill_path = target_skills_dir / name

    # Check if skill is installed
    if not (project_skill_path.exists() or project_skill_path.is_symlink()):
        scope = "global skills" if is_global else "this project"
        click.echo(f"Skill '{name}' is not installed in {scope}.")
        return

    # Remove the link
    remove_link(project_skill_path)

    scope = "global skills" if is_global else "project"
    click.echo(f"Removed {name} from {scope}.")
