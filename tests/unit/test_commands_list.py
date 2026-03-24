"""Tests for list command."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w
from click.testing import CliRunner

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.list import list_skills


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def initialized_repo(tmp_path: Path) -> Path:
    """Create an initialized repository with some skills."""
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

    # Create a test skill
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "v2026.03.23").mkdir()
    (skill_dir / "skill.yaml").write_text(
        "name = 'test-skill'\ndescription = 'A test skill'\n"
    )

    return repo_path


class TestListSkills:
    """Tests for list_skills function."""

    def test_list_skills_empty(self, tmp_path: Path) -> None:
        """Test list_skills returns empty list when no skills."""
        skills, warnings = list_skills(tmp_path)
        assert skills == []
        assert warnings == []

    def test_list_skills_with_skills(self, initialized_repo: Path) -> None:
        """Test list_skills returns skills info."""
        skills, warnings = list_skills(initialized_repo)
        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].description == "A test skill"
        assert skills[0].versions == 1
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
        assert "1 version" in result.output
