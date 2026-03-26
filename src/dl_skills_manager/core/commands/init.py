"""Initialize skills repository command."""

__all__ = ["init"]

import shutil
from datetime import datetime
from pathlib import Path

import click
import tomli_w

from dl_skills_manager.core.config import get_default_repo_path
from dl_skills_manager.core.exceptions import RepoAlreadyExistsError


def _get_latest_file_timestamp(skill_dir: Path) -> str:
    """Get timestamp from the most recently modified file in the directory."""
    latest_mtime = 0.0
    for file_path in skill_dir.rglob("*"):
        if file_path.is_file():
            mtime = file_path.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
    dt = datetime.fromtimestamp(latest_mtime)
    return dt.strftime("%Y%m%d%H%M%S")


def _backup_skill_to_bk(skill_dir: Path, bk_dir: Path) -> None:
    """Backup a skill folder to .bk directory with timestamp suffix."""
    skill_name = skill_dir.name
    timestamp = _get_latest_file_timestamp(skill_dir)
    backup_name = f"{skill_name}@{timestamp}"
    backup_path = bk_dir / backup_name
    shutil.copytree(skill_dir, backup_path, symlinks=False)


def _scan_and_backup_skills(skills_path: Path, bk_path: Path) -> list[str]:
    """Scan skills directory for folders containing SKILL.md and backup them.

    Returns list of skill names found.
    """
    skills_found: list[str] = []

    if not skills_path.exists():
        return skills_found

    for skill_dir in sorted(skills_path.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith("."):
            continue

        # Check if this directory contains SKILL.md
        if (skill_dir / "SKILL.md").exists():
            skills_found.append(skill_dir.name)
            _backup_skill_to_bk(skill_dir, bk_path)

    return skills_found


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

    if config_path.exists():
        raise RepoAlreadyExistsError(f"Config directory already exists at: {config_path}")

    # Determine skills storage path
    if skills_path is None:
        # Default: create ~/.skill-sync/skills/ subdirectory
        skills_storage_path = config_path / "skills"
    else:
        # Custom path: use directly as skills store root (no skills/ subdirectory)
        skills_storage_path = Path(skills_path).expanduser().resolve()

    # Create config directory
    try:
        config_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create config directory: {e}"
        ) from e

    # Create skills storage directory (if it doesn't exist)
    try:
        skills_storage_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create skills directory: {e}"
        ) from e

    # Create .bk backup directory
    bk_path = skills_storage_path / ".bk"
    try:
        bk_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RepoAlreadyExistsError(
            f"Failed to create .bk directory: {e}"
        ) from e

    # Scan existing skills and backup them
    skills_found = _scan_and_backup_skills(skills_storage_path, bk_path)

    # Create config.toml with [basic] section
    config_file = config_path / "config.toml"
    config_data = {
        "basic": {
            "path": str(config_path),
            "skills_store": str(skills_storage_path),
        },
        "settings": {
            "default_link_mode": link_mode,
        },
    }

    with config_file.open("wb") as f:
        tomli_w.dump(config_data, f)

    click.echo(f"Initialized config at: {config_path}")
    click.echo(f"Skills storage at: {skills_storage_path}")
    if skills_found:
        click.echo(f"Found {len(skills_found)} skill(s) and backed them up to .bk/: {', '.join(skills_found)}")
