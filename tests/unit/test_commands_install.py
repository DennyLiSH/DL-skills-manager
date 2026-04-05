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
        skills_store=repo_path / "data",
        default_link_mode="copy",
    )


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    """Create an initialized repository with a skill."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    data_dir = repo_path / "data"
    data_dir.mkdir()
    skills_subdir = data_dir / "skills"
    skills_subdir.mkdir()

    # Create config.toml with [basic] section
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {
                    "path": str(repo_path),
                    "skills_store": str(data_dir),
                },
                "settings": {
                    "default_link_mode": "copy",
                },
            },
            f,
        )

    # Create .bk directory
    bk_dir = data_dir / ".bk"
    bk_dir.mkdir()

    # Create a test skill
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
        assert "not found" in result.output.lower()

    def test_install_with_version(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a specific version from .bk."""
        # Create a history version in .bk
        bk_dir = repo_with_skill / "data" / ".bk"
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

    def test_install_nonexistent_version(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a nonexistent version raises error."""
        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "install",
                    "test-skill@v2099.99.99",
                    str(project_dir),
                ],
            )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

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


class TestInstallLinkMode:
    """Tests for install command link mode behavior."""

    def test_install_copy_mode_creates_directory(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test copy mode creates a regular directory."""
        mock_config = _make_mock_config(repo_with_skill)

        with patch(
            "dl_skills_manager.core.commands.install.load_config",
            return_value=mock_config,
        ):
            result = cli_runner.invoke(
                main,
                ["install", "test-skill", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        skill_path = project_dir / ".claude" / "skills" / "test-skill"
        assert skill_path.exists()
        assert skill_path.is_dir()
        assert not skill_path.is_symlink()

    def test_install_symlink_mode_calls_create_link(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test symlink mode calls create_link from linker module."""
        symlink_config = SkillSyncConfig(
            path=repo_with_skill,
            skills_store=repo_with_skill / "data",
            default_link_mode="symlink",
        )

        with (
            patch(
                "dl_skills_manager.core.commands.install.load_config",
                return_value=symlink_config,
            ),
            patch(
                "dl_skills_manager.core.commands.install.create_link",
            ) as mock_create_link,
        ):
            result = cli_runner.invoke(
                main,
                ["install", "test-skill", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        mock_create_link.assert_called_once()

    def test_install_link_mode_cli_override_to_symlink(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test --link-mode symlink overrides config default (copy)."""
        mock_config = _make_mock_config(repo_with_skill)

        with (
            patch(
                "dl_skills_manager.core.commands.install.load_config",
                return_value=mock_config,
            ),
            patch(
                "dl_skills_manager.core.commands.install.create_link",
            ) as mock_create_link,
        ):
            result = cli_runner.invoke(
                main,
                ["install", "--link-mode", "symlink", "test-skill", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        mock_create_link.assert_called_once()

    def test_install_link_mode_cli_override_to_copy(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test --link-mode copy overrides config default (symlink)."""
        symlink_config = SkillSyncConfig(
            path=repo_with_skill,
            skills_store=repo_with_skill / "data",
            default_link_mode="symlink",
        )

        with (
            patch(
                "dl_skills_manager.core.commands.install.load_config",
                return_value=symlink_config,
            ),
            patch(
                "dl_skills_manager.core.commands.install.install_skill_copy",
            ) as mock_install_copy,
        ):
            result = cli_runner.invoke(
                main,
                ["install", "--link-mode", "copy", "test-skill", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        mock_install_copy.assert_called_once()
