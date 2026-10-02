"""Shared utilities for CLI commands.

Provides common functionality used across multiple commands such as
repository path resolution and skill copy with backup/restore protection.
"""

import shutil
from collections.abc import Mapping
from pathlib import Path

from dl_skills_manager.core.agents import AgentDirOverride, resolve_agent_dirs
from dl_skills_manager.core.exceptions import LinkError, ValidationError
from dl_skills_manager.core.linker import copy_skill_dir

__all__ = [
    "resolve_command_target_dir",
    "resolve_skills_target_dir",
    "update_skill_copy",
]


def resolve_skills_target_dir(
    *,
    global_flag: bool,
    project_path: Path | None = None,
    agent: str = "claude",
    agent_overrides: Mapping[str, AgentDirOverride] | None = None,
) -> Path:
    """Resolve the target directory for skill installation.

    Args:
        global_flag: If True, resolve to the agent's global skills dir.
        project_path: Project path (required when global_flag is False).
        agent: Agent name (default "claude" for backward compatibility).
        agent_overrides: Config [agents] table, or None for builtin-only.

    Returns:
        Resolved target skills directory path.

    Raises:
        ValidationError: If agent is unknown, project_path is missing,
            or the agent does not support the requested scope.
    """
    global_dir, project_dir = resolve_agent_dirs(agent, agent_overrides)

    if global_flag:
        if global_dir is None:
            raise ValidationError(
                f"agent '{agent}' does not define a global skills directory"
            )
        # Resolve "~"-prefixed values through Path.home() instead of
        # expanduser(): expanduser() reads the USERPROFILE env var and
        # bypasses the Path.home seam that tests patch. Path.home() must
        # stay in this function for the same reason.
        if global_dir.startswith("~"):
            rel = global_dir[1:].lstrip("/\\")
            target = Path.home() / rel
        else:
            candidate = Path(global_dir)
            target = candidate if candidate.is_absolute() else Path.home() / candidate
    else:
        if project_path is None:
            raise ValidationError("project_path required for local installation")
        if project_dir is None:
            raise ValidationError(
                f"agent '{agent}' does not support project-level installation; "
                f"use --global"
            )
        target = project_path / project_dir

    target.mkdir(parents=True, exist_ok=True)
    return target


def resolve_command_target_dir(
    *,
    is_global: bool,
    project: str,
    agent: str = "claude",
    agent_overrides: Mapping[str, AgentDirOverride] | None = None,
) -> Path:
    """Resolve the target skills directory for a command invocation.

    Wraps resolve_skills_target_dir() with the --global/project/agent flag
    shape shared by install/update/remove/mklink.

    Args:
        is_global: If True, resolve the agent's global skills dir
            (project is ignored).
        project: Project path string (used when is_global is False).
        agent: Agent name (default "claude").
        agent_overrides: Config [agents] table, or None for builtin-only
            resolution (used by mklink).

    Returns:
        Resolved target skills directory path.

    Raises:
        ValidationError: Propagated from resolve_skills_target_dir for
            unknown agents, missing project scope, or invalid overrides.
    """
    if is_global:
        return resolve_skills_target_dir(
            global_flag=True, agent=agent, agent_overrides=agent_overrides
        )
    return resolve_skills_target_dir(
        global_flag=False,
        project_path=Path(project).resolve(),
        agent=agent,
        agent_overrides=agent_overrides,
    )


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
