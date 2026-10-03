"""Target skills directory resolution for CLI commands.

resolve_command_target_dir is a pure query (creates nothing);
ensure_target_dir expresses the "ready to write into" contract.
Write-path commands (install/update/mklink) chain both; read-path
commands (remove) resolve only.
"""

from collections.abc import Mapping
from pathlib import Path

from dl_skills_manager.core.agents import AgentDirOverride, resolve_agent_dirs
from dl_skills_manager.core.exceptions import ValidationError

__all__ = ["ensure_target_dir", "resolve_command_target_dir"]


def resolve_command_target_dir(
    *,
    is_global: bool,
    project: str,
    agent: str = "claude",
    agent_overrides: Mapping[str, AgentDirOverride] | None = None,
) -> Path:
    """Resolve the target skills directory for a command invocation.

    Pure query: agent registry lookup, [agents] config overrides,
    and scope validation. Creates nothing on disk.

    Args:
        is_global: If True, resolve the agent's global skills dir
            (project is ignored).
        project: Project path string (used when is_global is False).
        agent: Agent name (default "claude").
        agent_overrides: Config [agents] table, or None for builtin-only
            resolution (used by mklink).

    Returns:
        Resolved target skills directory path (not created).

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
        # expanduser(): Path.home() is the single documented home seam
        # (CLAUDE.md); expanduser() would drift to env-var-dependent
        # resolution instead of the seam that tests patch.
        if global_dir.startswith("~"):
            rel = global_dir[1:].lstrip("/\\")
            return Path.home() / rel
        candidate = Path(global_dir)
        return candidate if candidate.is_absolute() else Path.home() / candidate
    if project_dir is None:
        raise ValidationError(
            f"agent '{agent}' does not support project-level installation; use --global"
        )
    return Path(project).resolve() / project_dir


def ensure_target_dir(target_skills_dir: Path) -> Path:
    """Create the target skills directory (idempotent) and return it."""
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    return target_skills_dir
