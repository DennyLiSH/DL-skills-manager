"""Shared type definitions for DL Skills Manager."""

from dataclasses import dataclass, field

__all__ = [
    "InstalledSkill",
    "ProjectManifest",
    "SkillEntry",
    "SkillInfo",
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

    def __post_init__(self) -> None:
        """Validate skill data after initialization."""
        if self.name:
            if not all(c.isalnum() or c in "-_" for c in self.name):
                raise ValueError(f"Invalid skill name: {self.name}")


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
