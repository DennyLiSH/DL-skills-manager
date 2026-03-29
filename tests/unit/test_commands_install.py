"""Tests for install command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from dl_skills_manager.core.config import SkillSyncConfig

if TYPE_CHECKING:
    from click.testing import CliRunner


def _make_mock_config(repo_path: Path) -> SkillSyncConfig:
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "skills",
        default_link_mode="symlink",
    )


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    """Create an initialized repository with a skill."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    (repo_path / "skills").mkdir()

    # Create config.toml with [basic] section
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {
                    "path": str(repo_path),
                    "skills_store": str(repo_path / "skills"),
                },
                "settings": {
                    "default_link_mode": "symlink",
                },
            },
            f,
        )

    # Create .bk directory
    bk_dir = repo_path / "skills" / ".bk"
    bk_dir.mkdir()

    # Create a test skill
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")

    return repo_path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project directory."""
    project = tmp_path / "my-project"
    project.mkdir()
    return project


class TestInstallCommand:
    """Tests for install command."""

    def test_install_skill_to_project(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a skill to a project."""
        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "install",
                    "test-skill",
                    str(project_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Installed test-skill@latest" in result.output

        # Check skill was created
        skill_link = project_dir / ".claude" / "skills" / "test-skill"
        assert skill_link.exists()

    def test_install_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a skill that doesn't exist."""
        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "install",
                    "nonexistent",
                    str(project_dir),
                ],
            )

        assert result.exit_code != 0
        assert "does not exist" in result.output.lower()

    def test_install_with_version(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a specific version from .bk."""
        # Create a history version in .bk
        bk_dir = repo_with_skill / "skills" / ".bk"
        bk_version_dir = bk_dir / "test-skill@v2026.03.22"
        bk_version_dir.mkdir()
        (bk_version_dir / "SKILL.md").write_text("# Old Version\n")

        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "install",
                    "test-skill@v2026.03.22",
                    str(project_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "v2026.03.22" in result.output

    def test_install_global(
        self, cli_runner: CliRunner, repo_with_skill: Path, tmp_path: Path
    ) -> None:
        """Test installing a skill globally to ~/.claude/skills/."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        mock_config = _make_mock_config(repo_with_skill)

        with (
            patch(
                "dl_skills_manager.core.commands.install.load_config",
                return_value=mock_config,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.Path.home",
                return_value=fake_home,
            ),
        ):
            result = cli_runner.invoke(
                main,
                ["install", "--global", "test-skill"],
            )

        assert result.exit_code == 0, result.output
        assert "Installed test-skill@latest" in result.output

        # Check skill was installed to global location
        skill_link = fake_home / ".claude" / "skills" / "test-skill"
        assert skill_link.exists()

    def test_install_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test --global with explicit PROJECT path raises error."""
        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                ["install", "--global", "test-skill", str(project_dir)],
            )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output
