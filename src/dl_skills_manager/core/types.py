"""Shared type definitions for DL Skills Manager."""

from dataclasses import dataclass

__all__ = [
    "SkillInfo",
]


@dataclass(slots=True, frozen=True)
class SkillInfo:
    """Skill information for list output."""

    name: str
    history: tuple[str, ...]
