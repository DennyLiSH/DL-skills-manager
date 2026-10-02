"""Test helper utilities shared across test modules."""

from pathlib import Path

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.config import LinkMode, SkillSyncConfig


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
