"""Repository configuration management."""

__all__ = [
    "LinkMode",
    "RepoConfig",
    "create_default_config",
    "expand_path",
    "get_default_repo_path",
    "load_repo_config",
]

from dataclasses import dataclass
from pathlib import Path
from tomllib import TOMLDecodeError
from tomllib import load as load_toml
from typing import Literal

from dl_skills_manager.core.exceptions import ConfigError

type LinkMode = Literal["symlink", "hardlink", "copy"]


@dataclass(slots=True)
class RepoConfig:
    """Repository configuration."""

    name: str
    path: Path
    default_link_mode: LinkMode
    fallback_to_copy: bool


def expand_path(path_str: str) -> Path:
    """Expand ~ to user home directory."""
    return Path(path_str).expanduser()


def get_default_repo_path() -> Path:
    """Get the default skills repository path."""
    return Path.home() / ".skills-base"


def load_repo_config(repo_path: Path | None = None) -> RepoConfig:
    """Load repository configuration from config.toml.

    Args:
        repo_path: Path to the repository. Defaults to ~/.skills-base.

    Returns:
        RepoConfig instance.

    Raises:
        ConfigError: If config.toml cannot be read or parsed.
    """
    if repo_path is None:
        repo_path = get_default_repo_path()

    config_path = repo_path / "config.toml"

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with config_path.open("rb") as f:
            data = load_toml(f)
    except TOMLDecodeError as e:
        raise ConfigError(f"Failed to parse config.toml: {e}") from e

    repo_data = data.get("repo", {})
    settings_data = data.get("settings", {})

    return RepoConfig(
        name=repo_data.get("name", "my-skills"),
        path=expand_path(repo_data.get("path", str(repo_path))),
        default_link_mode=settings_data.get("default_link_mode", "symlink"),
        fallback_to_copy=settings_data.get("fallback_to_copy", True),
    )


def create_default_config(repo_path: Path) -> RepoConfig:
    """Create default repository configuration.

    Args:
        repo_path: Path to the repository.

    Returns:
        Default RepoConfig instance.
    """
    return RepoConfig(
        name="my-skills",
        path=repo_path,
        default_link_mode="symlink",
        fallback_to_copy=True,
    )
