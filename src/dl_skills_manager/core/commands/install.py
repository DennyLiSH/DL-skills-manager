"""Install skill command."""

__all__ = ["install"]

import click

from dl_skills_manager.core.commands._shared import resolve_command_target_dir
from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.linker import copy_skill_dir, create_link
from dl_skills_manager.core.store import SkillsStore, validate_skill_name


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
    depending on config or --link-mode override.

    Supports name@version syntax for specifying version directly in the name.

    Supports --agent to target non-Claude agent skills directories.

    Args:
        name: Name of the skill to install (optionally with @version suffix).
        project: Path to the project directory (default: current directory).
        is_global: If True, install to ~/.claude/skills/ globally.
        link_mode: Override the default link mode (force symlink instead of copy).
        agent: Target agent whose skills directory to install into.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    # Parse name@version syntax
    version: str | None = None
    if "@" in name:
        name, version = name.rsplit("@", 1)

    validate_skill_name(name)

    # Load config and determine effective link mode
    config = load_config()
    effective_mode = link_mode or "copy"

    # Find skill and version directories with validation
    store = SkillsStore(config.skills_store)
    version_dir = store.find_version(name, version)

    # Resolve target skills directory
    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )

    # Create symlink or copy based on effective mode
    project_skill_path = target_skills_dir / name

    if effective_mode == "symlink":
        create_link(version_dir, project_skill_path, force=True)
    else:
        copy_skill_dir(version_dir, project_skill_path, force=True)

    actual_version = version if version else "latest"
    click.echo(f"Installed {name}@{actual_version} to {project_skill_path}")
