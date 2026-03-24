"""Tests for install command."""

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
                "settings": {
                    "default_link_mode": "symlink",
                    "fallback_to_copy": True,
                },
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
                "version": "v2026.03.23-dev",
                "stable_version": "v2026.03.23",
            },
            f,
        )

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
        result = cli_runner.invoke(
            main,
            [
                "install",
                "test-skill",
                str(project_dir),
                "--repo",
                str(repo_with_skill),
            ],
        )

        assert result.exit_code == 0, result.output
        assert "Installed test-skill@v2026.03.23" in result.output

        # Check symlink was created
        skill_link = project_dir / ".claude" / "skills" / "test-skill"
        assert skill_link.exists()

    def test_install_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a skill that doesn't exist."""
        result = cli_runner.invoke(
            main,
            [
                "install",
                "nonexistent",
                str(project_dir),
                "--repo",
                str(repo_with_skill),
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_install_with_version(
        self, cli_runner: CliRunner, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """Test installing a specific version."""
        # Create a dev version
        skill_dir = repo_with_skill / "skills" / "test-skill"
        dev_version = skill_dir / "v2026.03.25-dev"
        dev_version.mkdir()
        (dev_version / "SKILL.md").write_text("# Dev Version\n")

        result = cli_runner.invoke(
            main,
            [
                "install",
                "test-skill",
                str(project_dir),
                "--repo",
                str(repo_with_skill),
                "--version",
                "v2026.03.25-dev",
            ],
        )

        assert result.exit_code == 0, result.output
        assert "v2026.03.25-dev" in result.output
