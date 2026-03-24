"""Custom exceptions for DL Skills Manager."""

__all__ = [
    "AppError",
    "ConfigError",
    "LinkError",
    "ManifestError",
    "RepoAlreadyExistsError",
    "RepoNotInitializedError",
    "SkillAlreadyExistsError",
    "SkillAlreadyInstalledError",
    "SkillNotFoundError",
    "ValidationError",
    "VersionNotFoundError",
    "WriteError",
]


class AppError(Exception):
    """Base exception for all application errors."""


class ConfigError(AppError):
    """Configuration file read or parse error."""


class LinkError(AppError):
    """Symlink or copy operation error."""


class ManifestError(AppError):
    """Project manifest read or write error."""


class SkillNotFoundError(AppError):
    """Skill does not exist in repository."""


class VersionNotFoundError(AppError):
    """Requested version does not exist."""


class SkillAlreadyInstalledError(AppError):
    """Skill is already installed in project."""


class SkillAlreadyExistsError(AppError):
    """Skill already exists in repository."""


class RepoNotInitializedError(AppError):
    """Repository is not initialized."""


class RepoAlreadyExistsError(AppError):
    """Repository already exists."""


class WriteError(AppError):
    """File write operation failed."""


class ValidationError(AppError):
    """Input validation failed."""
