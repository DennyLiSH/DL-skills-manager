"""Shared type definitions for DL Skills Manager."""

from dataclasses import dataclass

__all__ = [
    "InstalledSkill",
    "SkillInfo",
]


@dataclass(slots=True, frozen=True)
class SkillInfo:
    """Skill information for list output."""

    name: str
    description: str
    version: str
    history: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class InstalledSkill:
    """An installed skill entry."""

    name: str
    source: str
    version: str
