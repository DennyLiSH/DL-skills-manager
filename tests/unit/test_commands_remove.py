"""Tests for remove command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
        output_lower = result.output.lower()
        assert "not installed" in output_lower or "removed" in output_lower
