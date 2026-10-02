"""Target skills directory resolution for CLI commands."""

from collections.abc import Mapping
from pathlib import Path

from dl_skills_manager.core.agents import AgentDirOverride, resolve_agent_dirs
from dl_skills_manager.core.exceptions import ValidationError

__all__ = ["resolve_command_target_dir"]


def resolve_command_target_dir(
    *,
    is_global: bool,
    project: str,
    agent: str = "claude",
    agent_overrides: Mapping[str, AgentDirOverride] | None = None,
) -> Path:
    """Resolve the target skills directory for a command invocation.

    Single entry point for install/update/remove/mklink target
    resolution: agent registry lookup, [agents] config overrides,
    scope validation, and target dir creation.

    Args:
        is_global: If True, resolve the agent's global skills dir
            (project is ignored).
        project: Project path string (used when is_global is False).
        agent: Agent name (default "claude").
        agent_overrides: Config [agents] table, or None for builtin-only
            resolution (used by mklink).

    Returns:
        Resolved target skills directory path (created if missing).

    Raises:
        ValidationError: Unknown agent, agent without the requested
            scope, or invalid [agents] override values.
    """
    global_dir, project_dir = resolve_agent_dirs(agent, agent_overrides)

    if is_global:
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
        if project_dir is None:
            raise ValidationError(
                f"agent '{agent}' does not support project-level installation; "
                f"use --global"
            )
        target = Path(project).resolve() / project_dir

    target.mkdir(parents=True, exist_ok=True)
    return target
