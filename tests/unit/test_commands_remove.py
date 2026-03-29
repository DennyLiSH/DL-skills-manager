"""Tests for remove command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def project_with_skill(tmp_path: Path) -> Path:
    """Create a project with an installed skill."""
    project = tmp_path / "my-project"
    project.mkdir()

    # Create .claude/skills directory and skill
    skill_dir = project / ".claude" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")

    # Create skills.toml manifest
    manifest_path = project / ".claude" / "skills.toml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    skill_source = tmp_path / ".skills-repo" / "skills" / "test-skill"
    with manifest_path.open("wb") as f:
        tomli_w.dump(
            {
                "skills": {
                    "test-skill": {
                        "source": str(skill_source),
                        "version": "v2026.03.23",
                    }
                }
            },
            f,
        )

    return project


class TestRemoveCommand:
    """Tests for remove command."""

    def test_remove_skill_from_project(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill from a project."""
        skill_link = project_with_skill / ".claude" / "skills" / "test-skill"
        assert skill_link.exists()

        result = cli_runner.invoke(
            main,
            ["remove", "test-skill", str(project_with_skill)],
        )

        assert result.exit_code == 0, result.output
        assert "Removed test-skill" in result.output

    def test_remove_nonexistent_skill(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill that isn't installed."""
        result = cli_runner.invoke(
            main,
            ["remove", "nonexistent-skill", str(project_with_skill)],
        )

        # Should still exit 0 but warn
        assert "not installed" in result.output.lower()

    def test_remove_invalid_name(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill with path traversal in name."""
        result = cli_runner.invoke(
            main,
            ["remove", "../evil", str(project_with_skill)],
        )

        assert result.exit_code != 0

    def test_remove_global(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test removing a skill from global ~/.claude/skills/."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        global_skills = fake_home / ".claude" / "skills"
        skill_dir = global_skills / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n")

        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = cli_runner.invoke(
                main,
                ["remove", "--global", "test-skill"],
            )

        assert result.exit_code == 0, result.output
        assert "Removed test-skill from global skills" in result.output
        assert not skill_dir.exists()

    def test_remove_global_nonexistent(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test removing a nonexistent global skill."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = cli_runner.invoke(
                main,
                ["remove", "--global", "nonexistent"],
            )

        assert "not installed in global skills" in result.output

    def test_remove_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test --global with explicit PROJECT path raises error."""
        result = cli_runner.invoke(
            main,
            ["remove", "--global", "test-skill", str(project_with_skill)],
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output
