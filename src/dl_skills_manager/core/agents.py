"""Built-in agent skills directory registry and resolution."""

__all__ = [
    "BUILTIN_AGENTS",
    "AgentDirOverride",
    "AgentSpec",
    "resolve_agent_dirs",
]

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dl_skills_manager.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Directory layout for a built-in agent.

    global_dir: '~'-prefixed, absolute, or home-relative path string
        (POSIX style, e.g. ".claude/skills").
    project_dir: project-root-relative path string, or None when the
        agent has no project-level skills directory.
    """

    global_dir: str
    project_dir: str | None


@dataclass(frozen=True, slots=True)
class AgentDirOverride:
    """[agents.<name>] config override; None fields inherit the builtin value."""

    global_dir: str | None = None
    project_dir: str | None = None


BUILTIN_AGENTS: dict[str, AgentSpec] = {
    "claude": AgentSpec(global_dir=".claude/skills", project_dir=".claude/skills"),
    "codex": AgentSpec(global_dir=".agents/skills", project_dir=".agents/skills"),
    "pi": AgentSpec(global_dir=".pi/agent/skills", project_dir=".pi/skills"),
    "zcode": AgentSpec(global_dir=".zcode/skills", project_dir=".zcode/skills"),
    "workbuddy": AgentSpec(global_dir=".workbuddy/skills", project_dir=None),
}


def _normalize_project_dir(value: str) -> str:
    """Validate a project_dir value and return its POSIX-style form."""
    if not value.strip():
        raise ValidationError("agents project_dir must not be empty")
    if value != value.strip():
        raise ValidationError(
            f"agents project_dir values must not have leading/trailing "
            f"whitespace (got {value!r})"
        )
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    has_drive = len(normalized) >= 2 and normalized[1] == ":"
    if (
        normalized.startswith(("/", "~"))
        or has_drive
        or ".." in parts
        or "." in parts
    ):
        raise ValidationError(
            f"agents project_dir must be a relative path without '.' or '..' "
            f"(got {value!r})"
        )
    if any(":" in part for part in parts):
        raise ValidationError(
            f"agents project_dir values must not contain ':' (got {value!r})"
        )
    return normalized


def _normalize_global_dir(value: str) -> str:
    """Validate a global_dir value and return its POSIX-style form."""
    if not value.strip():
        raise ValidationError("agents global_dir must not be empty")
    if value != value.strip():
        raise ValidationError(
            f"agents global_dir values must not have leading/trailing "
            f"whitespace (got {value!r})"
        )
    value = value.replace("\\", "/")
    if value.startswith("~"):
        # Reject bare "~" and "~name" forms: only "~/" is well-defined here
        # (expanduser semantics for "~name" are not wanted).
        if not value.startswith("~/"):
            raise ValidationError(
                f"agents global_dir '~' values must start with '~/' (got {value!r})"
            )
        rel = value[2:].strip("/")
        if not rel:
            raise ValidationError(
                f"agents global_dir '~/' values must include a path under "
                f"the home directory (got {value!r})"
            )
        parts = rel.split("/")
        if "." in parts or ".." in parts:
            # Bare "." segments ("~/." ) resolve to the home root — the same
            # effect as a bare "~/" that this hardening rejects.
            raise ValidationError(
                f"agents global_dir values must not contain '.' or '..' "
                f"(got {value!r})"
            )
        if any(":" in part for part in parts):
            # A drive-bearing segment ("~/d:secret", "~/c:..") resets
            # Path.home() joins on Windows and escapes the home boundary.
            raise ValidationError(
                f"agents global_dir values must not contain ':' (got {value!r})"
            )
        return "~/" + rel
    has_drive = len(value) >= 2 and value[1] == ":"
    candidate = Path(value)
    if has_drive and not candidate.is_absolute():
        raise ValidationError(
            f"agents global_dir drive-relative values are not allowed (got {value!r})"
        )
    parts = value.split("/")
    if any(":" in part for i, part in enumerate(parts) if not (i == 0 and has_drive)):
        raise ValidationError(
            f"agents global_dir values must not contain ':' (got {value!r})"
        )
    if not candidate.is_absolute() and (".." in parts or "." in parts):
        raise ValidationError(
            f"agents global_dir relative values must not contain '.' or '..' "
            f"(got {value!r})"
        )
    return value


def resolve_agent_dirs(
    agent: str,
    agent_overrides: Mapping[str, AgentDirOverride] | None = None,
) -> tuple[str | None, str | None]:
    """Resolve an agent's directory layout, merging config overrides.

    Args:
        agent: Agent name (builtin or config-defined).
        agent_overrides: Config-provided [agents] table, or None for
            builtin-only resolution (used by mklink).

    Returns:
        (global_dir, project_dir); either may be None when unsupported.

    Raises:
        ValidationError: Unknown agent, custom agent without any dir,
            or invalid project_dir value.
    """
    overrides = agent_overrides or {}
    spec = BUILTIN_AGENTS.get(agent)
    override = overrides.get(agent)

    if spec is None:
        if override is None:
            known = sorted({*BUILTIN_AGENTS, *overrides})
            raise ValidationError(
                f"Unknown agent '{agent}'. Available agents: {', '.join(known)}"
            )
        global_dir = override.global_dir
        project_dir = override.project_dir
        if global_dir is None and project_dir is None:
            raise ValidationError(
                f"Agent '{agent}' must define global_dir or project_dir "
                f"in [agents.{agent}]"
            )
    else:
        global_dir = spec.global_dir
        project_dir = spec.project_dir
        if override is not None:
            if override.global_dir is not None:
                global_dir = override.global_dir
            if override.project_dir is not None:
                project_dir = override.project_dir

    if project_dir is not None:
        project_dir = _normalize_project_dir(project_dir)
    if global_dir is not None:
        global_dir = _normalize_global_dir(global_dir)

    return global_dir, project_dir
