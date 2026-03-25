"""Initialize skills repository command."""

__all__ = ["init"]

from pathlib import Path

import click
import tomli_w

from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.exceptions import RepoAlreadyExistsError


@click.command()
@click.option(
    "--skills-path",
    type=click.Path(),
    default=None,
    help="Path to skills storage (default: ~/.skill-sync/skills/)",
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

    if config_path.exists():
        raise RepoAlreadyExistsError(f"Config directory already exists at: {config_path}")

    # Determine skills storage path
    if skills_path is None:
        skills_storage_path = config_path / "skills"
    else:
        skills_storage_path = Path(skills_path).expanduser().resolve()

    # Create config directory
    try:
        config_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create config directory: {e}"
        ) from e

    # Create skills storage directory
    try:
        skills_storage_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create skills directory: {e}"
        ) from e

    # Create config.toml
    config_file = config_path / "config.toml"
    config_data = {
        "repo": {
            "name": "my-skills",
            "skills_path": str(skills_storage_path),
        },
        "settings": {
            "default_link_mode": link_mode,
            "fallback_to_copy": True,
        },
    }

    with config_file.open("wb") as f:
        tomli_w.dump(config_data, f)

    click.echo(f"Initialized config at: {config_path}")
    click.echo(f"Skills storage at: {skills_storage_path}")
