"""DL Skills Manager - Claude Code Skills Repository Manager.

Centralized skill repository with on-demand linking to projects.
Reduces system-level directory token consumption by separating skill
storage from loading directories.
"""

from dl_skills_manager.cli import main
from dl_skills_manager.core.exceptions import (
    AppError,
    ConfigError,
    LinkError,
    ManifestError,
    SkillAlreadyExistsError,
    SkillAlreadyInstalledError,
    SkillNotFoundError,
    ValidationError,
    VersionNotFoundError,
)

__all__ = [
    "AppError",
    "ConfigError",
    "LinkError",
    "ManifestError",
    "SkillAlreadyExistsError",
    "SkillAlreadyInstalledError",
    "SkillNotFoundError",
    "ValidationError",
    "VersionNotFoundError",
    "main",
]

__version__ = "0.1.0"
