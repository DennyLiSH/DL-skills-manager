"""Shared type definitions for DL Skills Manager."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "InstalledSkill",
    "ProjectManifest",
    "SkillEntry",
    "SkillInfo",
    "SkillMetadata",
    "SkillYamlData",
]


@dataclass(slots=True, frozen=True)
class SkillEntry:
    """Single skill entry in project manifest."""

    source: str
    version: str


@dataclass(slots=True, frozen=True)
class ProjectManifest:
    """Project manifest structure mapping skill names to entries."""

    skills: dict[str, SkillEntry] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class SkillYamlData:
    """skill.yaml structure."""

    name: str = ""
    description: str = ""
    version: str = ""
    stable_version: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""


@dataclass(slots=True, frozen=True)
class SkillInfo:
    """Skill information for list output."""

    name: str
    description: str
    versions: int


@dataclass(slots=True)
class InstalledSkill:
    """An installed skill entry."""

    name: str
    source: str
    version: str


@dataclass(slots=True)
class SkillMetadata:
    """Skill metadata from skill.yaml."""

    name: str = ""
    description: str = ""
    version: str = ""
    stable_version: str = ""
    author: str = ""
    created: str = ""
    updated: str = ""
    tags: list[str] = field(default_factory=list)
