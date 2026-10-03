"""mklink command - batch symlink skills from an arbitrary source directory."""

from pathlib import Path

import click

from dl_skills_manager.core.commands._options import (
    reject_global_with_project,
    target_options,
)
from dl_skills_manager.core.commands.targets import (
    ensure_target_dir,
    resolve_command_target_dir,
)
from dl_skills_manager.core.linker import create_link
from dl_skills_manager.core.store import is_skill_dir, validate_skill_name

__all__ = ["link_skills", "mklink"]


def link_skills(
    source_dir: Path,
    *,
    prefix: str,
    is_global: bool,
    project: str,
    agent: str,
) -> list[str]:
    """Batch-link valid skills from source_dir into the target skills dir.

    Never reads config: agent resolution is builtin-registry-only
    (command contract, see guard tests test_mklink_ignores_agents_config*).

    Args:
        source_dir: Directory whose skill subdirs (containing SKILL.md)
            get linked.
        prefix: Namespace prefix for link names (may be empty).
        is_global: Target the agent's global skills dir.
        project: Project path string (used when is_global is False).
        agent: Agent name (builtin registry only).

    Returns:
        Names of the created links, in source order.

    Raises:
        ValidationError: Invalid prefixed name or unknown agent.
        LinkError: Symlink/copy failure.
    """
    target_dir = ensure_target_dir(
        resolve_command_target_dir(
            is_global=is_global, project=project, agent=agent
        )
    )

    linked: list[str] = []
    for subdir in sorted(source_dir.iterdir()):
        if subdir.name.startswith("."):
            continue
        if not is_skill_dir(subdir):
            continue

        link_name = prefix + subdir.name
        validate_skill_name(link_name)
        create_link(subdir, target_dir / link_name, force=True)
        linked.append(link_name)
    return linked


@click.command()
@click.argument("source_path", type=click.Path(exists=True, file_okay=False))
@target_options(
    agent_help="Target agent dir (builtin registry only, no [agents] config)."
)
@click.option("--prefix", default="", help="Symlink name prefix (e.g. 'gstack-')")
def mklink(
    source_path: str,
    project: str,
    prefix: str,
    *,
    is_global: bool,
    agent: str,
) -> None:
    """Batch symlink skills from SOURCE_PATH to project's .claude/skills/.

    Scans SOURCE_PATH for subdirectories containing SKILL.md and creates
    symlinks (or copies on Windows without symlink privilege) in the
    project's .claude/skills/ directory.

    Use --agent to target other agents' skills dirs (builtin registry only).
    Use --prefix to namespace linked skills (e.g. --prefix gstack-).
    Use --global to link to ~/.claude/skills/ instead.
    """
    reject_global_with_project(is_global=is_global, project=project)

    source_dir = Path(source_path).resolve()

    linked = link_skills(
        source_dir,
        prefix=prefix,
        is_global=is_global,
        project=project,
        agent=agent,
    )

    for name in linked:
        click.echo(f"Linked {name}")
    click.echo(f"Linked {len(linked)} skill(s) from {source_dir}")
