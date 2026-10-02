"""Install skill command."""

__all__ = ["install", "install_skill"]

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import resolve_command_target_dir
from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.linker import copy_skill_dir, create_link
from dl_skills_manager.core.store import SkillsStore, validate_skill_name


def install_skill(
    name: str,
    *,
    version: str | None,
    is_global: bool,
    project: str,
    link_mode: str | None,
    agent: str,
    config: SkillSyncConfig,
) -> Path:
    """Install a skill into the resolved target directory.

    Copy is the default; link_mode="symlink" creates a symlink instead.
    config.default_link_mode is deliberately not consulted (ADR 0001).

    Args:
        name: Skill name (validated).
        version: Optional version to install (None = latest).
        is_global: Target the agent's global skills dir.
        project: Project path string (used when is_global is False).
        link_mode: "symlink" or "copy"; None means copy.
        agent: Agent name.
        config: Pre-loaded repository config.

    Returns:
        Path to the installed skill.

    Raises:
        SkillNotFoundError: Skill missing from the repository.
        VersionNotFoundError: Requested version missing.
        ValidationError: Invalid name/agent/scope.
        LinkError: Symlink or copy failure.
    """
    version_dir = SkillsStore(config.skills_store).find_version(name, version)

    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )
    project_skill_path = target_skills_dir / name

    if (link_mode or "copy") == "symlink":
        create_link(version_dir, project_skill_path, force=True)
    else:
        copy_skill_dir(version_dir, project_skill_path, force=True)
    return project_skill_path


@click.command()
@click.argument("name")  # format: skill-name[@version]
@click.argument("project", default=".")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    default=False,
    help="Install to ~/.claude/skills/ instead of a project.",
)
@click.option(
    "--link-mode",
    type=click.Choice(["symlink", "copy"]),
    default=None,
    help="Override default link mode (symlink or copy) for this installation.",
)
@click.option(
    "--agent",
    default="claude",
    show_default=True,
    help="Target agent dir (claude/codex/pi/zcode/workbuddy or [agents]).",
)
def install(
    name: str,
    project: str,
    *,
    is_global: bool,
    link_mode: str | None,
    agent: str,
) -> None:
    """Install a skill into the current project.

    Creates a symlink or copies the skill to .claude/skills/{skill_name},
    depending on --link-mode (copy is the default).

    Supports name@version syntax for specifying version directly in the name.

    Supports --agent to target non-Claude agent skills directories.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Parse name@version syntax
    version: str | None = None
    if "@" in name:
        name, version = name.rsplit("@", 1)

    validate_skill_name(name)

    config = load_config()
    dest = install_skill(
        name,
        version=version,
        is_global=is_global,
        project=project,
        link_mode=link_mode,
        agent=agent,
        config=config,
    )

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {dest}")
