"""Initialize skills repository command."""

__all__ = ["init"]

from pathlib import Path

import click
import tomli_w

from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.exceptions import (
    ConfigError,
    RepoAlreadyExistsError,
    WriteError,
)


@click.command()
@click.option(
    "--skills-path",
    type=click.Path(),
    default=None,
    help="Path to skills storage root (default: ~/.skill-sync/skills/)",
)
@click.option(
    "--link-mode",
    type=click.Choice(["symlink", "copy"]),
    default="symlink",
    help="Default link mode for skill installation (default: symlink)",
)
def init(skills_path: str | None, link_mode: str) -> None:
    """Initialize a new skills repository.

    Creates the config directory at ~/.skill-sync/ and skills storage directory.
    """
    # Always use ~/.skill-sync/ as config directory
    config_path = get_default_repo_path()

    # Check if already initialized
    config_file = config_path / "config.toml"
    if config_file.exists():
        raise RepoAlreadyExistsError(f"Repository already initialized at {config_path}")

    # Determine skills storage path
    if skills_path is None:
        # Default: create ~/.skill-sync/skills/ subdirectory
        skills_storage_path = config_path / "skills"
    else:
        # Custom path: use directly as skills store root (no skills/ subdirectory)
        skills_storage_path = Path(skills_path).expanduser().resolve()

    # Create directories
    try:
        config_path.mkdir(parents=True, exist_ok=True)
        skills_storage_path.mkdir(parents=True, exist_ok=True)
        bk_path = skills_storage_path / ".bk"
        bk_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ConfigError(f"Failed to create directory: {e}") from e

    # Create config.toml with [basic] section
    config_data = {
        "basic": {
            "path": str(config_path),
            "skills_store": str(skills_storage_path),
        },
        "settings": {
            "default_link_mode": link_mode,
        },
    }

    try:
        with config_file.open("wb") as f:
            tomli_w.dump(config_data, f)
    except OSError as e:
        raise WriteError(f"Failed to write config: {config_file}") from e

    click.echo(f"Initialized config at: {config_path}")
    click.echo(f"Skills storage at: {skills_storage_path}")
