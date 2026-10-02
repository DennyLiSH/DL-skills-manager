"""Skills store: single owner of the repository layout and backup naming.

All knowledge of the on-disk layout (skills/, .dev/, .bk/) and the
backup naming convention ({name}@{version}) lives here. Callers go
through the SkillsStore interface instead of assembling paths.
"""

__all__ = ["SKILL_MARKER", "Promotion", "SkillsStore", "validate_skill_name"]

import re
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from dl_skills_manager.core.exceptions import (
    SkillNotFoundError,
    ValidationError,
    VersionNotFoundError,
    WriteError,
)
from dl_skills_manager.core.types import SkillInfo

SKILL_MARKER = "SKILL.md"

# vYYYY.MM.DD[.N][-suffix] — the only version forms the store accepts.
_VERSION_PATTERN = re.compile(r"v\d{4}\.\d{2}\.\d{2}(?:\.\d+)?(?:-[\w.]+)?")


def validate_skill_name(name: str) -> None:
    """Validate skill name format.

    Raises:
        ValidationError: If skill name contains invalid characters or patterns.
    """
    # Check path traversal patterns first for proper error messages
    if ".." in name or name.startswith(("~", "/", "\\", "$")):
        raise ValidationError(f"Invalid skill name: {name}")
    if "/" in name or "\\" in name:
        raise ValidationError(f"Invalid skill name: {name}")
    if not all(c.isalnum() or c in "-_" for c in name):
        raise ValidationError(
            "Skill name must be alphanumeric, hyphens, or underscores"
        )


@dataclass(frozen=True, slots=True)
class Promotion:
    """Result of promoting a dev skill to production."""

    name: str
    version: str
    target: Path
    backup: Path


class SkillsStore:
    """Deep module over the skills store directory layout."""

    def __init__(self, skills_store: Path) -> None:
        self._root = skills_store.resolve()

    @property
    def root(self) -> Path:
        """Resolved store root."""
        return self._root

    # -- path queries --

    def skills_dir(self) -> Path:
        """Production skills directory (latest versions)."""
        return self._root / "skills"

    def skill_dir(self, name: str) -> Path:
        """Validated path of a production skill directory."""
        validate_skill_name(name)
        skill_dir = self.skills_dir() / name
        try:
            resolved = skill_dir.resolve()
        except OSError as e:
            raise ValidationError(f"Could not resolve skill path: {skill_dir}") from e
        if not resolved.is_relative_to(self._root):
            raise ValidationError(f"Skill path escaped repository: {name}")
        return skill_dir

    def dev_dir(self, name: str) -> Path:
        """Development directory of a skill.

        Unvalidated path query: callers must validate_skill_name(name)
        first (promote/find_version do; new callers must too).
        """
        return self._root / ".dev" / name

    def backups_dir(self) -> Path:
        """History backups directory."""
        return self._root / ".bk"

    def backup_dir(self, name: str, version: str) -> Path:
        """Backup directory for one skill version ({name}@{version}).

        Unvalidated path query: callers must validate_skill_name(name)
        and version-form first (find_version/next_backup_version do).
        """
        return self.backups_dir() / f"{name}@{version}"

    # -- queries --

    def find_skill(self, name: str) -> Path:
        """Locate an existing production skill.

        Raises:
            SkillNotFoundError: If skill does not exist in repository.
            ValidationError: If skill name contains path traversal attempts.
        """
        skill_dir = self.skill_dir(name)
        if not skill_dir.exists():
            raise SkillNotFoundError(f"Skill '{name}' not found in repository")
        return skill_dir

    def find_version(self, name: str, version: str | None = None) -> Path:
        """Locate the directory for a skill version.

        version=None resolves to the latest (production) directory; a
        specific version checks the skill dir first, then .bk backups.

        Raises:
            SkillNotFoundError: If the skill does not exist.
            ValidationError: If the version contains path characters
                (legitimate versions never do).
            VersionNotFoundError: If the requested version does not exist.
        """
        skill_dir = self.find_skill(name)
        if version is None:
            return skill_dir
        # Whitelist: legit versions never contain path metacharacters,
        # drive-relative segments ("C:evil" resets pathlib joins on
        # Windows), empty strings, or "." — all of which either escape
        # the store or silently resolve to the wrong directory.
        if _VERSION_PATTERN.fullmatch(version) is None:
            raise ValidationError(f"Invalid version: {version}")
        requested = skill_dir / version
        if requested.exists():
            return requested
        backup = self.backup_dir(name, version)
        if backup.exists():
            return backup
        raise VersionNotFoundError(
            f"Version '{version}' not found for skill '{name}'"
        )

    def list_backups(self, name: str) -> list[str]:
        """Version strings of a skill's backups, newest first."""
        bk_dir = self.backups_dir()
        if not bk_dir.exists():
            return []
        prefix = f"{name}@"
        versions = [
            entry.name[len(prefix) :]
            for entry in bk_dir.iterdir()
            if entry.is_dir() and entry.name.startswith(prefix)
        ]
        return sorted(versions, reverse=True)

    def list_skills(self) -> list[SkillInfo]:
        """All valid production skills (dirs containing SKILL.md)."""
        skills_subdir = self.skills_dir()
        if not skills_subdir.exists():
            return []

        history_by_skill: dict[str, list[str]] = {}
        bk_dir = self.backups_dir()
        if bk_dir.exists():
            for entry in sorted(bk_dir.iterdir()):
                if entry.is_dir() and "@" in entry.name:
                    skill_name, version = entry.name.split("@", 1)
                    history_by_skill.setdefault(skill_name, []).append(version)

        skills: list[SkillInfo] = []
        for skill_dir in sorted(skills_subdir.iterdir()):
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / SKILL_MARKER).exists():
                continue
            history = sorted(history_by_skill.get(skill_dir.name, []), reverse=True)
            skills.append(SkillInfo(name=skill_dir.name, history=tuple(history)))
        return skills

    # -- writes --

    def next_backup_version(self, name: str) -> str:
        """Next backup version for a dev skill: vYYYY.MM.DD, .N on collision.

        The date comes from the newest file mtime under .dev/{name}.
        """
        latest_mtime = 0.0
        for file_path in self.dev_dir(name).rglob("*"):
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
        dt = datetime.fromtimestamp(latest_mtime, tz=UTC)
        base_version = dt.strftime("v%Y.%m.%d")

        indices: list[int] = []
        for version in self.list_backups(name):
            if version == base_version:
                indices.append(0)
            elif version.startswith(f"{base_version}."):
                suffix = version[len(base_version) + 1 :]
                if suffix.isdigit():
                    indices.append(int(suffix))
        if not indices:
            return base_version
        return f"{base_version}.{max(indices) + 1}"

    def promote(self, name: str) -> Promotion:
        """Move a skill from .dev to production with a versioned backup.

        Raises:
            ValidationError: If the name is invalid.
            SkillNotFoundError: If .dev/{name} is missing or has no SKILL.md.
            WriteError: If the copy operations fail.
        """
        validate_skill_name(name)
        dev_dir = self.dev_dir(name)
        if not dev_dir.exists() or not dev_dir.is_dir():
            raise SkillNotFoundError(f"Skill '{name}' not found in .dev/ directory")
        if not (dev_dir / SKILL_MARKER).exists():
            raise SkillNotFoundError(f"Skill '{name}' in .dev/ has no SKILL.md")

        self.backups_dir().mkdir(parents=True, exist_ok=True)
        version = self.next_backup_version(name)
        target = self.skill_dir(name)
        backup = self.backup_dir(name, version)

        try:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(dev_dir, target, symlinks=False)
            shutil.copytree(dev_dir, backup, symlinks=False)
        except OSError as e:
            raise WriteError(f"Failed to move '{name}' to production: {e}") from e

        return Promotion(name=name, version=version, target=target, backup=backup)
