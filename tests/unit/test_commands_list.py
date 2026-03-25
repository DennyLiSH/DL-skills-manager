"""Tests for list command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.list import list_skills

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def initialized_repo(tmp_path: Path) -> Path:
    """Create an initialized repository with some skills.

    Creates the new architecture:
    - tmp_path/.skill-sync/config.toml (config dir)
    - tmp_path/.skill-sync/skills/ (skills storage)
    """
    config_dir = tmp_path / ".skill-sync"
    config_dir.mkdir()
    skills_dir = config_dir / "skills"
    skills_dir.mkdir()

    # Create config.toml with skills_store
    config_path = config_dir / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "repo": {"name": "test", "skills_store": str(skills_dir)},
                "settings": {"default_link_mode": "symlink", "fallback_to_copy": True},
            },
            f,
        )

    # Create a test skill (must contain SKILL.md to be recognized)
    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")

    # Create a history version in .bk
    bk_dir = skills_dir / ".bk"
    bk_dir.mkdir()
    bk_skill_dir = bk_dir / "test-skill@v2026.03.22"
    bk_skill_dir.mkdir()
    (bk_skill_dir / "SKILL.md").write_text("# Test Skill Old\n")

    return config_dir


class TestListSkills:
    """Tests for list_skills function."""

    def test_list_skills_empty(self, tmp_path: Path) -> None:
        """Test list_skills returns empty list when no skills."""
        # Create proper config structure
        config_dir = tmp_path / ".skill-sync"
        config_dir.mkdir()
        skills_dir = config_dir / "skills"
        skills_dir.mkdir()
        config_path = config_dir / "config.toml"
        with config_path.open("wb") as f:
            tomli_w.dump(
                {
                    "repo": {"name": "test", "skills_store": str(skills_dir)},
                    "settings": {"default_link_mode": "symlink", "fallback_to_copy": True},
                },
                f,
            )

        skills, warnings = list_skills(config_dir)
        assert skills == []
        assert warnings == []

    def test_list_skills_with_skills(self, initialized_repo: Path) -> None:
        """Test list_skills returns skills info."""
        skills, warnings = list_skills(initialized_repo)
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].description == ""
        assert skills[0].version == "current"
        assert skills[0].history == ("v2026.03.22",)
        assert warnings == []


class TestListCommand:
    """Tests for list command."""

    def test_list_no_repo(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test list with non-existent repo."""
        # Point to a path that doesn't exist
        result = cli_runner.invoke(
            main, ["list", "--repo", str(tmp_path / "nonexistent")]
        )
        assert result.exit_code == 1

    def test_list_with_skills(
        self, cli_runner: CliRunner, initialized_repo: Path
    ) -> None:
        """Test list shows skills."""
        result = cli_runner.invoke(main, ["list", "--repo", str(initialized_repo)])

        assert result.exit_code == 0
        assert "test-skill" in result.output
        assert "1 history" in result.output
