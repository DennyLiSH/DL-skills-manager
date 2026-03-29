"""Tests for update command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from test_helpers import mock_config

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    """Create a repository with a skill."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    data_dir = repo_path / "data"
    data_dir.mkdir()
    skills_subdir = data_dir / "skills"
    skills_subdir.mkdir()

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(repo_path), "skills_store": str(data_dir)},
                "settings": {"default_link_mode": "symlink"},
            },
            f,
        )

    # Create skill
    skill_dir = skills_subdir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")

    return repo_path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project directory."""
    project = tmp_path / "my-project"
    project.mkdir()
    return project


class TestUpdateCommand:
    """Tests for update command."""

    def test_update_skill(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test updating a skill to latest."""
        # Install old version first
        old_skill = project_dir / ".claude" / "skills" / "test-skill"
        old_skill.mkdir(parents=True)
        (old_skill / "SKILL.md").write_text("# Old Version\n")

        mock_cfg = mock_config(repo_with_skill)
        with (
            patch(
                "dl_skills_manager.core.commands.update.load_config",
                return_value=mock_cfg,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_cfg,
            ),
        ):
            result = cli_runner.invoke(
                main,
                ["update", "test-skill", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        assert "Updated test-skill" in result.output

    def test_update_nonexistent_skill(
        self,
        cli_runner: CliRunner,
        repo_with_skill: Path,
        project_dir: Path,
    ) -> None:
        """Test updating a skill that doesn't exist."""
        mock_cfg = mock_config(repo_with_skill)
        with (
            patch(
                "dl_skills_manager.core.commands.update.load_config",
                return_value=mock_cfg,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_cfg,
            ),
        ):
            result = cli_runner.invoke(
                main,
                ["update", "nonexistent", str(project_dir)],
            )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_update_global(
        self, cli_runner: CliRunner, repo_with_skill: Path, tmp_path: Path
    ) -> None:
        """Test updating a skill globally."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        # Pre-install old version in global dir
        global_skills = fake_home / ".claude" / "skills"
        old_skill = global_skills / "test-skill"
        old_skill.mkdir(parents=True)
        (old_skill / "SKILL.md").write_text("# Old Version\n")

        mock_cfg = mock_config(repo_with_skill)
        with (
            patch(
                "dl_skills_manager.core.commands.update.load_config",
                return_value=mock_cfg,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_cfg,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.Path.home",
                return_value=fake_home,
            ),
        ):
            result = cli_runner.invoke(
                main,
                ["update", "--global", "test-skill"],
            )

        assert result.exit_code == 0, result.output
        assert "Updated test-skill" in result.output

    def test_update_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test --global with explicit PROJECT path raises error."""
        mock_cfg = mock_config(repo_with_skill)
        with patch(
            "dl_skills_manager.core.commands.update.load_config",
            return_value=mock_cfg,
        ):
            result = cli_runner.invoke(
                main,
                ["update", "--global", "test-skill", str(project_dir)],
            )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output
