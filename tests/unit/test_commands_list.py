"""Tests for list command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.list import list_skills
from dl_skills_manager.core.config import SkillSyncConfig

if TYPE_CHECKING:
    from click.testing import CliRunner


def _mock_config(repo_path: Path) -> SkillSyncConfig:
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "skills",
        default_link_mode="copy",
    )


@pytest.fixture
def initialized_repo(tmp_path: Path) -> Path:
    """Create an initialized repository with some skills."""
    config_dir = tmp_path / ".skill-sync"
    config_dir.mkdir()
    skills_dir = config_dir / "skills"
    skills_dir.mkdir()

    # Create config.toml
    config_path = config_dir / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(config_dir), "skills_store": str(skills_dir)},
                "settings": {"default_link_mode": "symlink"},
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
        config_dir = tmp_path / ".skill-sync"
        config_dir.mkdir()
        skills_dir = config_dir / "skills"
        skills_dir.mkdir()
        config_path = config_dir / "config.toml"
        with config_path.open("wb") as f:
            tomli_w.dump(
                {
                    "basic": {
                        "path": str(config_dir),
                        "skills_store": str(skills_dir),
                    },
                    "settings": {"default_link_mode": "symlink"},
                },
                f,
            )

        mock_cfg = _mock_config(config_dir)
        with patch(
            "dl_skills_manager.core.commands.list.load_config",
            return_value=mock_cfg,
        ):
            skills, warnings = list_skills()
        assert skills == []
        assert warnings == []

    def test_list_skills_with_skills(self, initialized_repo: Path) -> None:
        """Test list_skills returns skills info."""
        mock_cfg = _mock_config(initialized_repo)
        with patch(
            "dl_skills_manager.core.commands.list.load_config",
            return_value=mock_cfg,
        ):
            skills, warnings = list_skills()
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].description == ""
        assert skills[0].version == "current"
        assert skills[0].history == ("v2026.03.22",)
        assert warnings == []


class TestListCommand:
    """Tests for list CLI command."""

    def test_list_no_repo(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test list with non-existent config."""
        config_dir = tmp_path / ".skill-sync"
        config_dir.mkdir()
        (config_dir / "skills").mkdir()
        # No config.toml → load_config will fail

        with patch(
            "dl_skills_manager.core.config.get_default_repo_path",
            return_value=config_dir,
        ):
            result = cli_runner.invoke(main, ["list"])
        assert result.exit_code == 1

    def test_list_with_skills(
        self, cli_runner: CliRunner, initialized_repo: Path
    ) -> None:
        """Test list shows skills."""
        mock_cfg = _mock_config(initialized_repo)
        with patch(
            "dl_skills_manager.core.commands.list.load_config",
            return_value=mock_cfg,
        ):
            result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "test-skill" in result.output
        assert "1 history" in result.output
