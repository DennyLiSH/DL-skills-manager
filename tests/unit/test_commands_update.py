"""Tests for update command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
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
def repo_with_skill(tmp_path: Path) -> Path:
    """Create a repository with a skill."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    skills_dir = repo_path / "skills"
    skills_dir.mkdir()

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(repo_path), "skills_store": str(skills_dir)},
                "settings": {"default_link_mode": "symlink"},
            },
            f,
        )

    # Create skill
    skill_dir = skills_dir / "test-skill"
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

        mock_cfg = _mock_config(repo_with_skill)
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
        mock_cfg = _mock_config(repo_with_skill)
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
