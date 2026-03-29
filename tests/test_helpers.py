"""Test helper utilities shared across test modules."""

from pathlib import Path

from dl_skills_manager.core.config import SkillSyncConfig


def mock_config(repo_path: Path) -> SkillSyncConfig:
    """Create a mock SkillSyncConfig pointing to a temporary repo."""
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "data",
        default_link_mode="copy",
    )
