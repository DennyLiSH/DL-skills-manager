"""Shared type definitions for DL Skills Manager."""

from typing import TypedDict

__all__ = [
    "ProjectManifest",
    "SkillEntry",
    "SkillInfo",
    "SkillYamlData",
]


class SkillEntry(TypedDict):
    """Single skill entry in project manifest."""

    source: str
    version: str


class ProjectManifest(TypedDict):
    """Project manifest structure mapping skill names to entries."""

    skills: dict[str, SkillEntry]


class SkillYamlData(TypedDict, total=False):
    """skill.yaml structure - fields are optional since file may not exist."""

    name: str
    description: str
    version: str
    stable_version: str
    author: str
    tags: list[str]
    created: str
    updated: str


class SkillInfo(TypedDict):
    """Skill information for list output."""

    name: str
    description: str
    versions: int
