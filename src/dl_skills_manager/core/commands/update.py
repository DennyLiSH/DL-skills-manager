"""Update skill command."""

__all__ = ["update", "update_skill"]

import shutil
from dataclasses import dataclass
from pathlib import Path

import click

from dl_skills_manager.core.commands._options import (
    reject_global_with_project,
    target_options,
)
from dl_skills_manager.core.commands.targets import resolve_command_target_dir
from dl_skills_manager.core.config import SkillSyncConfig, load_config
from dl_skills_manager.core.exceptions import LinkError, WriteError
from dl_skills_manager.core.linker import copy_skill_dir
from dl_skills_manager.core.store import SkillsStore


@dataclass(frozen=True, slots=True)
class UpdateOutcome:
    """Result of an update attempt."""

    skipped: bool
    path: Path | None = None
    symlink_target: Path | None = None


def update_skill(
    name: str,
    *,
    is_global: bool,
    project: str,
    agent: str,
    config: SkillSyncConfig,
) -> UpdateOutcome:
    """Update a copy-installed skill to the latest stable version.

    Symlink installs are skipped: the symlink already points at the
    repository source (the caller decides how to report that).

    Args:
        name: Skill name.
        is_global: Target the agent's global skills dir.
        project: Project path string (used when is_global is False).
        agent: Agent name.
        config: Pre-loaded repository config.

    Returns:
        UpdateOutcome describing skip (with symlink target) or the
        updated install path.

    Raises:
        SkillNotFoundError: Skill missing from the repository.
        ValidationError: Unknown agent or unsupported scope.
        LinkError: Copy failure (after backup/restore protection).
    """
    target_skills_dir = resolve_command_target_dir(
        is_global=is_global,
        project=project,
        agent=agent,
        agent_overrides=config.agent_dirs,
    )
    version_dir = SkillsStore(config.skills_store).find_version(name)

    installed = target_skills_dir / name
    if installed.is_symlink():
        return UpdateOutcome(skipped=True, symlink_target=installed.resolve())

    update_skill_copy(target_skills_dir, name, version_dir)
    return UpdateOutcome(skipped=False, path=installed)


def update_skill_copy(
    target_skills_dir: Path,
    name: str,
    version_dir: Path,
) -> Path:
    """Update a skill with backup/restore protection.

    Creates a backup before updating. If the update fails, restores
    from backup. Backup is deleted on success.

    Args:
        target_skills_dir: Path to the target skills directory.
        name: Skill name.
        version_dir: Path to the version directory to copy.

    Returns:
        Path to the updated skill copy.

    Raises:
        LinkError: If the update operation fails.
    """
    project_skill_path = target_skills_dir / name
    backup_path = target_skills_dir / f"{name}.bk"

    # Remove any stale backup from previous failed update
    if backup_path.exists():
        shutil.rmtree(backup_path)

    # Create backup of current installation if it exists
    if project_skill_path.exists():
        shutil.copytree(project_skill_path, backup_path)

    try:
        copy_skill_dir(version_dir, project_skill_path, force=True)
        # Success - delete backup
        if backup_path.exists():
            shutil.rmtree(backup_path)
        return project_skill_path
    except LinkError:
        # Failure - restore from backup
        if backup_path.exists():
            if project_skill_path.exists():
                shutil.rmtree(project_skill_path)
            shutil.move(str(backup_path), str(project_skill_path))
        raise


@click.command()
@click.argument("name")
@target_options()
def update(name: str, project: str, *, is_global: bool, agent: str) -> None:
    """Update a skill to the latest stable version.

    Re-copies the latest version from the repository. If the skill was
    installed as a symlink, the update is skipped since the symlink already
    points to the latest repository source.
    """
    reject_global_with_project(is_global=is_global, project=project)

    config = load_config()

    outcome = update_skill(
        name, is_global=is_global, project=project, agent=agent, config=config
    )

    if outcome.skipped:
        assert outcome.symlink_target is not None  # noqa: S101
        click.echo(
            f"Skill '{name}' is installed as symlink -> {outcome.symlink_target}"
        )
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

    click.echo(f"Updated {name} to latest")
