"""Tests for bump command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    """Create an initialized repository with a skill."""
    repo_path = tmp_path / ".skills-repo"
    repo_path.mkdir()
    (repo_path / "skills").mkdir()
    (repo_path / "templates").mkdir()

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "repo": {"name": "test", "path": str(repo_path)},
                "settings": {"default_link_mode": "symlink", "fallback_to_copy": True},
            },
            f,
        )

    # Create a test skill with version
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()
    version_dir = skill_dir / "v2026.03.23"
    version_dir.mkdir()
    (version_dir / "SKILL.md").write_text("# Test Skill\n")

    # Create skill.yaml
    skill_yaml = skill_dir / "skill.yaml"
    with skill_yaml.open("wb") as f:
        tomli_w.dump(
            {
                "name": "test-skill",
                "description": "A test skill",
                "version": "v2026.03.23",
                "stable_version": "v2026.03.23",
            },
            f,
        )

    return repo_path


class TestBumpCommand:
    """Tests for bump command."""

    def test_bump_creates_dev_version(
        self, cli_runner: CliRunner, repo_with_skill: Path
    ) -> None:
        """Test creating a new dev version."""
        result = cli_runner.invoke(
            main,
            ["bump", "test-skill", "--repo", str(repo_with_skill)],
        )

        assert result.exit_code == 0, result.output
        assert "-dev" in result.output

        skill_dir = repo_with_skill / "skills" / "test-skill"
        # Should have v2026.03.23 (old) and v{date}-dev (new)
        version_list = [
            v.name for v in skill_dir.iterdir() if v.is_dir() and v.name.startswith("v")
        ]
        assert any(v.endswith("-dev") for v in version_list)

    def test_bump_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_skill: Path
    ) -> None:
        """Test bumping a skill that doesn't exist."""
        result = cli_runner.invoke(
            main,
            ["bump", "nonexistent", "--repo", str(repo_with_skill)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
