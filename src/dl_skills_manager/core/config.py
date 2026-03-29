"""Repository configuration management."""

__all__ = [
    "LinkMode",
    "SkillSyncConfig",
    "create_default_config",
    "expand_path",
    "get_default_repo_path",
    "load_config",
]

from dataclasses import dataclass
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml
from typing import Literal

from dl_skills_manager.core.exceptions import ConfigError

type LinkMode = Literal["symlink", "copy"]


@dataclass(slots=True)
class SkillSyncConfig:
    """Repository configuration."""

    path: Path
    skills_store: Path
    default_link_mode: LinkMode  # TBD


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

    default_link_mode = settings_data.get("default_link_mode", "symlink")
    if default_link_mode not in ("symlink", "copy"):
        raise ConfigError(
            f"Invalid default_link_mode '{default_link_mode}' in config.toml. "
            "Must be 'symlink' or 'copy'."
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

    return SkillSyncConfig(
        path=path,
        skills_store=skills_store,
        default_link_mode=default_link_mode,
    )


def create_default_config(repo_path: Path, skills_store: Path) -> SkillSyncConfig:
    """Create default repository configuration.

    Args:
        repo_path: Path to the config directory.
        skills_store: Path to the skills storage directory.

    Returns:
        Default SkillSyncConfig instance.
    """
    return SkillSyncConfig(
        path=repo_path,
        skills_store=skills_store,
        default_link_mode="symlink",
    )
