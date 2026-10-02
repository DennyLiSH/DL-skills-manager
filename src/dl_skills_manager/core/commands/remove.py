"""Remove skill command."""

__all__ = ["remove", "remove_skill"]

import click

from dl_skills_manager.core.commands._shared import resolve_command_target_dir
from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.linker import remove_link
from dl_skills_manager.core.store import validate_skill_name


def remove_skill(
    name: str,
    *,
    is_global: bool,
    project: str,
    agent: str,
    config: SkillSyncConfig,
) -> bool:
    """Remove an installed skill from a project or agent skills dir.

    Args:
        name: Skill name.
        is_global: Target the agent's global skills dir.
        project: Project path string (used when is_global is False).
        agent: Agent name.
        config: Pre-loaded repository config ([agents] overrides).

    Returns:
        True if a skill was removed; False if nothing was installed.

    Raises:
        ValidationError: Invalid skill name, unknown agent, or
            unsupported scope.
    """
    validate_skill_name(name)

    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )
    skill_path = target_skills_dir / name

    if not (skill_path.exists() or skill_path.is_symlink()):
        return False

    remove_link(skill_path)
    return True


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

    # Validate before load_config to keep CLI error precedence stable
    # (invalid name reports as ValidationError even without a repo).
    validate_skill_name(name)

    config = load_config()

    removed = remove_skill(
        name, is_global=is_global, project=project, agent=agent, config=config
    )

    if not removed:
        scope = "global skills" if is_global else "this project"
        click.echo(f"Skill '{name}' is not installed in {scope}.")
        return
    scope = "global skills" if is_global else "project"
    click.echo(f"Removed {name} from {scope}.")
