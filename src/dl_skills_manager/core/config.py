"""Repository configuration management."""

__all__ = [
    "LinkMode",
    "SkillSyncConfig",
    "expand_path",
    "get_default_repo_path",
    "load_config",
]

import logging
from dataclasses import dataclass, field
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml
from typing import Literal

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.exceptions import ConfigError

type LinkMode = Literal["symlink", "copy"]

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SkillSyncConfig:
    """Repository configuration."""

    path: Path
    skills_store: Path
    agent_dirs: dict[str, AgentDirOverride] = field(default_factory=dict)


def expand_path(path_str: str) -> Path:
    """Expand ~ to user home directory."""
    return Path(path_str).expanduser()


def get_default_repo_path() -> Path:
    """Get the default config directory path."""
    return Path.home() / ".skill-sync"


def load_config() -> SkillSyncConfig:
    """Load repository configuration from config.toml.

    Returns:
        SkillSyncConfig instance.

    Raises:
        ConfigError: If config.toml cannot be read or parsed.
    """
    repo_path = get_default_repo_path()

    config_path = repo_path / "config.toml"

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with config_path.open("rb") as f:
            data = load_toml(f)
    except TOMLDecodeError as e:
        raise ConfigError(f"Failed to parse config.toml: {e}") from e

    basic_data = data.get("basic", {})
    settings_data = data.get("settings", {})
    if "default_link_mode" in settings_data:
        logger.warning(
            "config.toml [settings] default_link_mode "
            f"({settings_data['default_link_mode']!r}) is no longer used; "
            "install always defaults to copy (override per-invocation "
            "with --link-mode)"
        )

    # Load skills_store from config, default to ~/.skill-sync/skills/
    skills_store_str = basic_data.get("skills_store", None)
    if skills_store_str:
        skills_store = expand_path(skills_store_str)
    else:
        skills_store = repo_path / "data"

    # Load path from config, default to repo_path
    path_str = basic_data.get("path", None)
    if path_str:
        path = expand_path(path_str)
    else:
        path = repo_path

    agents_data = data.get("agents", {})
    agent_dirs: dict[str, AgentDirOverride] = {}
    for agent_name, entry in agents_data.items():
        if not isinstance(entry, dict):
            raise ConfigError(f"Invalid [agents.{agent_name}] entry: expected a table")
        global_dir = entry.get("global_dir")
        project_dir = entry.get("project_dir")
        if global_dir is not None and not isinstance(global_dir, str):
            raise ConfigError(f"[agents.{agent_name}] global_dir must be a string")
        if project_dir is not None and not isinstance(project_dir, str):
            raise ConfigError(f"[agents.{agent_name}] project_dir must be a string")
        agent_dirs[str(agent_name)] = AgentDirOverride(
            global_dir=global_dir, project_dir=project_dir
        )

    return SkillSyncConfig(
        path=path,
        skills_store=skills_store,
        agent_dirs=agent_dirs,
    )
