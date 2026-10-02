"""Test helper utilities shared across test modules."""

from pathlib import Path
from typing import TYPE_CHECKING

from dl_skills_manager.core.config import LinkMode, SkillSyncConfig

if TYPE_CHECKING:
    from dl_skills_manager.core.agents import AgentDirOverride


def mock_config(
    repo_path: Path,
    *,
    agent_dirs: dict[str, AgentDirOverride] | None = None,
    default_link_mode: LinkMode = "copy",
) -> SkillSyncConfig:
    """Create a SkillSyncConfig pointing at a temporary repo."""
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "data",
        default_link_mode=default_link_mode,
        agent_dirs=agent_dirs or {},
    )
