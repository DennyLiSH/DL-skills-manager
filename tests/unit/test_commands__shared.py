"""Unit tests for core.commands._shared module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.commands._shared import (
    find_skill_dir,
    find_version_dir,
    resolve_repo_path,
)
from dl_skills_manager.core.exceptions import (
    ConfigError,
    SkillNotFoundError,
    VersionNotFoundError,
)


class TestFindSkillDir:
    """Tests for find_skill_dir function."""

    def test_find_skill_dir_valid(self, skills_repo_dir: Path) -> None:
        """Test finding an existing skill."""
        # skills_repo_dir is .skill-sync with config.toml
        # Create a skill in the skills directory
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        result = find_skill_dir(skills_repo_dir, "test-skill")
        assert result == skill_dir

    def test_find_skill_dir_not_found(self, skills_repo_dir: Path) -> None:
        """Test error when skill does not exist."""
        skills_dir = skills_repo_dir / "skills"
        # No skills created

        with pytest.raises(SkillNotFoundError, match="not found"):
            find_skill_dir(skills_repo_dir, "nonexistent")

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
        # skills_repo_dir fixture already creates skills/ directory
        with pytest.raises(ValueError, match=expected_match):
            find_skill_dir(skills_repo_dir, skill_name)


class TestResolveRepoPath:
    """Tests for resolve_repo_path function."""

    def test_resolve_repo_path_with_config_error(self, tmp_path: Path) -> None:
        """Test that ConfigError is handled and non-existent path raises."""
        with patch(
            "dl_skills_manager.core.commands._shared.load_repo_config",
            side_effect=ConfigError("Not a config"),
        ):
            # When path doesn't exist, should raise ConfigError
            non_existent = tmp_path / "nonexistent"
            with pytest.raises(ConfigError, match="does not exist"):
                resolve_repo_path(str(non_existent))

    def test_resolve_repo_path_with_existing_non_config_dir(
        self, tmp_path: Path
    ) -> None:
        """Test that existing directory without config raises ConfigError."""
        existing_dir = tmp_path / "existing-repo"
        existing_dir.mkdir()

        with patch(
            "dl_skills_manager.core.commands._shared.load_repo_config",
            side_effect=ConfigError("Not a config"),
        ), pytest.raises(ConfigError, match="not initialized"):
            resolve_repo_path(str(existing_dir))


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

    def test_find_version_dir_no_versions(self, skills_repo_dir: Path) -> None:
        """Test error when no versions exist."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        with pytest.raises(VersionNotFoundError, match="No version found"):
            find_version_dir(skill_dir)

    def test_find_version_dir_with_malformed_yaml(self, skills_repo_dir: Path) -> None:
        """Test that malformed skill.yaml falls back to version directory."""
        skills_dir = skills_repo_dir / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        version_dir = skill_dir / "v2026.03.23"
        version_dir.mkdir()

        # Create malformed skill.yaml
        skill_yaml = skill_dir / "skill.yaml"
        skill_yaml.write_bytes(b"invalid: toml: content: [")

        # Should fall back to the version directory
        result = find_version_dir(skill_dir)
        assert result == version_dir
