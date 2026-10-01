"""Update skill command."""

__all__ = ["update"]

import click

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    resolve_command_target_dir,
    update_skill_copy,
)
from dl_skills_manager.core.config import load_config


@click.command()
@click.argument("name")
@click.argument("project", default=".")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    default=False,
    help="Update skill in ~/.claude/skills/ instead of a project.",
)
@click.option(
    "--agent",
    default="claude",
    show_default=True,
    help="Target agent dir (claude/codex/pi/zcode/workbuddy or [agents]).",
)
def update(name: str, project: str, *, is_global: bool, agent: str) -> None:
    """Update a skill to the latest stable version.

    Re-copies the latest version from the repository. If the skill was
    installed as a symlink, the update is skipped since the symlink already
    points to the latest repository source.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Load config first: [agents] overrides affect target dir resolution
    config = load_config()

    # Resolve target skills directory
    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )

    # Find skill and version directories (update always uses stable/latest)
    skill_dir = find_skill_dir(name, config=config)
    version_dir = find_version_dir(skill_dir, version=None)

    # Check if skill is installed as symlink — skip update
    project_skill_link = target_skills_dir / name
    if project_skill_link.is_symlink():
        resolved = project_skill_link.resolve()
        click.echo(f"Skill '{name}' is installed as symlink -> {resolved}")
        click.echo("No update needed — symlink points directly to repository source.")
        reinstall_flags: list[str] = []
        if is_global:
            reinstall_flags.append("--global")
        if agent != "claude":
            reinstall_flags.append(f"--agent {agent}")
        flag_suffix = f" {' '.join(reinstall_flags)}" if reinstall_flags else ""
        click.echo(
            f"To reinstall: skill-sync remove {name}{flag_suffix} && "
            f"skill-sync install {name}{flag_suffix}"
        )
        return

    # Copy-installed skill: perform overwrite update
    update_skill_copy(
        target_skills_dir,
        name,
        skill_dir,
        version_dir,
    )

    click.echo(f"Updated {name} to latest")
