"""Initialize skills repository command."""

__all__ = ["InitResult", "init", "init_repo"]

from dataclasses import dataclass
from pathlib import Path

import click
import tomli_w

from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.exceptions import (
    ConfigError,
    RepoAlreadyExistsError,
    WriteError,
)


@dataclass(frozen=True, slots=True)
class InitResult:
    """Paths created by init_repo."""

    repo_path: Path
    skills_store: Path


def init_repo(
    *,
    skills_path: str | None,
    repo_path: Path,
) -> InitResult:
    """Create the repository directory structure and config.toml.

    Args:
        skills_path: Custom skills storage root, or None for the
            default {repo_path}/data.
        repo_path: Repository config directory (~/.skill-sync).

    Returns:
        InitResult with the repo path and skills store path.

    Raises:
        RepoAlreadyExistsError: If config.toml already exists.
        ConfigError: If directory creation fails.
        WriteError: If config.toml cannot be written.
    """
    config_file = repo_path / "config.toml"
    if config_file.exists():
        raise RepoAlreadyExistsError(f"Repository already initialized at {repo_path}")

    if skills_path is None:
        skills_storage_path = repo_path / "data"
    else:
        skills_storage_path = Path(skills_path).expanduser().resolve()

    try:
        repo_path.mkdir(parents=True, exist_ok=True)
        skills_storage_path.mkdir(parents=True, exist_ok=True)
        for sub in ("skills", ".dev", ".bk", "agents"):
            (skills_storage_path / sub).mkdir(parents=True, exist_ok=True)
        claude_plugin_path = skills_storage_path / ".claude-plugin"
        claude_plugin_path.mkdir(parents=True, exist_ok=True)
        (claude_plugin_path / "marketplace.json").write_text("{}")
    except OSError as e:
        raise ConfigError(f"Failed to create directory: {e}") from e

    config_data = {
        "basic": {
            "path": str(repo_path),
            "skills_store": str(skills_storage_path),
        },
    }

    try:
        with config_file.open("wb") as f:
            tomli_w.dump(config_data, f)
    except OSError as e:
        raise WriteError(f"Failed to write config: {config_file}") from e

    return InitResult(repo_path=repo_path, skills_store=skills_storage_path)


@click.command()
@click.option(
    "--skills-path",
    type=click.Path(),
    default=None,
    help="Path to skills storage root (default: ~/.skill-sync/data/)",
)
def init(skills_path: str | None) -> None:
    """Initialize a new skills repository.

    Creates the config directory at ~/.skill-sync/ and skills storage directory.
    Skills are installed as copies by default (see ADR 0001); use
    install --link-mode symlink per invocation when needed.
    """
    repo_path = get_default_repo_path()

    # Check before any work so an existing repo errors immediately.
    if (repo_path / "config.toml").exists():
        raise RepoAlreadyExistsError(f"Repository already initialized at {repo_path}")

    result = init_repo(skills_path=skills_path, repo_path=repo_path)

    click.echo(f"Initialized config at: {result.repo_path}")
    click.echo(f"Skills storage at: {result.skills_store}")
