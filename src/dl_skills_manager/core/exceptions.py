"""Custom exceptions for DL Skills Manager."""

__all__ = [
    "AppError",
    "ConfigError",
    "LinkError",
    "RepoAlreadyExistsError",
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


class SkillNotFoundError(AppError):
    """Skill does not exist in repository."""


class VersionNotFoundError(AppError):
    """Requested version does not exist."""


class RepoAlreadyExistsError(AppError):
    """Repository already exists."""


class WriteError(AppError):
    """File write operation failed."""


class ValidationError(AppError):
    """Input validation failed."""
