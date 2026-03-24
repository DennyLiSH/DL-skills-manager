"""Initialize skills repository command."""

__all__ = ["init"]

from pathlib import Path

import click
import tomli_w

from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.exceptions import RepoAlreadyExistsError


@click.command()
@click.option(
    "--path",
    type=click.Path(),
    default=None,
    help="Path to initialize repository (default: ~/.skills-base)",
)
@click.option(
    "--link-mode",
    type=click.Choice(["symlink", "copy"]),
    default="symlink",
    help="Default link mode for skill installation (default: symlink)",
)
def init(path: str | None, link_mode: str) -> None:
    """Initialize a new skills repository.

    Creates the repository directory structure and config.toml.
    """
    if path is None:
        repo_path = get_default_repo_path()
    else:
        repo_path = Path(path).expanduser().resolve()

    if repo_path.exists():
        raise RepoAlreadyExistsError(f"Repository already exists at: {repo_path}")

    # Create directory structure atomically
    try:
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "skills").mkdir(parents=True, exist_ok=True)
        (repo_path / "templates").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create repository directory: {e}"
        ) from e

    # Verify skills directory was created
    if not (repo_path / "skills").exists():
        raise RepoAlreadyExistsError("Failed to create skills directory")

    # Create config.toml
    config_path = repo_path / "config.toml"
    config_data = {
        "repo": {
            "name": "my-skills",
            "path": str(repo_path),
        },
        "settings": {
            "default_link_mode": link_mode,
            "fallback_to_copy": True,
        },
    }

    with config_path.open("wb") as f:
        tomli_w.dump(config_data, f)

    click.echo(f"Initialized skills repository at: {repo_path}")
