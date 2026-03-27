"""Move skill from .dev to production."""

__all__ = ["mtp"]

import re
import shutil
from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    get_latest_file_timestamp,
    validate_skill_name,
)
from dl_skills_manager.core.config import load_config
from dl_skills_manager.core.exceptions import SkillNotFoundError


def _resolve_version(dev_dir: Path, name: str, bk_dir: Path) -> str:
    """Resolve version string from dev dir's latest file timestamp.

    Format: vYYYY.MM.DD, with .N suffix for same-day duplicates.

    Args:
        dev_dir: Path to .dev/{skill-name}.
        name: Skill name.
        bk_dir: Path to .bk directory.

    Returns:
        Version string like 'v2026.03.28' or 'v2026.03.28.1'.
    """
    timestamp = get_latest_file_timestamp(dev_dir)
    # Parse "YYYYMMDDHHMMSS" -> "YYYY.MM.DD"
    date_part = f"{timestamp[:4]}.{timestamp[4:6]}.{timestamp[6:8]}"
    base_version = f"v{date_part}"

    # Check for existing backups with same base version
    if not bk_dir.exists():
        return base_version

    existing_indices: list[int] = []
    pattern = re.compile(
        re.escape(name) + r"@" + re.escape(base_version) + r"(?:\.(\d+))?$"
    )
    for entry in bk_dir.iterdir():
        m = pattern.match(entry.name)
        if m:
            suffix = m.group(1)
            existing_indices.append(int(suffix) if suffix else 0)

    if not existing_indices:
        return base_version

    # Next available suffix
    next_idx = max(existing_indices) + 1
    return f"{base_version}.{next_idx}"


@click.command()
@click.argument("name")
def mtp(name: str) -> None:
    """Move a skill from .dev to production.

    Copies the skill from .dev/{name} to the skills store root and
    creates a versioned backup in .bk/.
    """
    validate_skill_name(name)

    config = load_config()
    skills_store = config.skills_store.resolve()

    dev_dir = skills_store / ".dev" / name
    if not dev_dir.exists() or not dev_dir.is_dir():
        raise SkillNotFoundError(
            f"Skill '{name}' not found in .dev/ directory"
        )
    if not (dev_dir / "SKILL.md").exists():
        raise SkillNotFoundError(
            f"Skill '{name}' in .dev/ has no SKILL.md"
        )

    bk_dir = skills_store / ".bk"
    bk_dir.mkdir(parents=True, exist_ok=True)

    version = _resolve_version(dev_dir, name, bk_dir)

    target = skills_store / name
    if target.exists():
        shutil.rmtree(target)

    shutil.copytree(dev_dir, target, symlinks=False)

    bk_target = bk_dir / f"{name}@{version}"
    shutil.copytree(dev_dir, bk_target, symlinks=False)

    click.echo(f"Moved '{name}' to production (version: {version})")
    click.echo(f"  -> {target}")
    click.echo(f"  -> {bk_target}")
