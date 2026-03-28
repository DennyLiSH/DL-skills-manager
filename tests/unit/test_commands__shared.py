"""Unit tests for core.commands._shared module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
)
from dl_skills_manager.core.config import SkillSyncConfig
from dl_skills_manager.core.exceptions import (
    SkillNotFoundError,
    VersionNotFoundError,
)


def _mock_config(repo_path: Path) -> SkillSyncConfig:
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "skills",
        default_link_mode="copy",
    )


class TestFindSkillDir:
    """Tests for find_skill_dir function."""

    def test_find_skill_dir_valid(self, skills_repo_dir: Path) -> None:
        """Test finding an existing skill."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        with patch(
            "dl_skills_manager.core.commands._shared.load_config",
            return_value=_mock_config(skills_repo_dir),
        ):
            result = find_skill_dir("test-skill")
        assert result == skill_dir

    def test_find_skill_dir_not_found(self, skills_repo_dir: Path) -> None:
        """Test error when skill does not exist."""
        with (
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=_mock_config(skills_repo_dir),
            ),
            pytest.raises(SkillNotFoundError, match="not found"),
        ):
            find_skill_dir("nonexistent")

    @pytest.mark.parametrize(
        "skill_name,expected_match",
        [
            ("../etc", "Invalid skill name"),
            ("/etc", "Invalid skill name"),
            ("\\etc", "Invalid skill name"),
            ("test-skill/../test-skill", "Invalid skill name"),
        ],
    )
    def test_find_skill_dir_path_traversal_rejected(
        self, skills_repo_dir: Path, skill_name: str, expected_match: str
    ) -> None:
        """Test path traversal attempts are rejected."""
        with pytest.raises(ValueError, match=expected_match):
            find_skill_dir(skill_name)


class TestFindVersionDir:
    """Tests for find_version_dir function."""

    def test_find_version_dir_specific_version(self, skills_repo_dir: Path) -> None:
        """Test finding a specific version directory."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        version_dir = skill_dir / "v2026.03.23"
        version_dir.mkdir()

        result = find_version_dir(skill_dir, "v2026.03.23")
        assert result == version_dir

    def test_find_version_dir_specific_not_found(self, skills_repo_dir: Path) -> None:
        """Test error when specific version does not exist."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        with pytest.raises(VersionNotFoundError, match="not found"):
            find_version_dir(skill_dir, "v2026.03.23")

    def test_find_version_dir_latest_returns_skill_dir(
        self, skills_repo_dir: Path
    ) -> None:
        """Test that no version specified returns the skill dir itself (latest)."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        result = find_version_dir(skill_dir)
        assert result == skill_dir

    def test_find_version_dir_from_bk(self, skills_repo_dir: Path) -> None:
        """Test finding a version from .bk/ directory."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        bk_dir = skills_dir / ".bk"
        bk_dir.mkdir()
        bk_version = bk_dir / "test-skill@v2026.03.20"
        bk_version.mkdir()

        result = find_version_dir(skill_dir, "v2026.03.20")
        assert result == bk_version
