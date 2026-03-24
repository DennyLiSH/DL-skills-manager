"""Tests for status command."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w
from click.testing import CliRunner

from dl_skills_manager.cli import main


@pytest.fixture
def project_with_skills(tmp_path: Path) -> Path:
    """Create a project with installed skills."""
    project = tmp_path / "my-project"
    project.mkdir()

    # Create skills.toml manifest with multiple skills
    # Note: manifest path is .claude/skills/skills.toml
    manifest_dir = project / ".claude" / "skills"
    manifest_dir.mkdir(parents=True)
    manifest_path = manifest_dir / "skills.toml"
    with manifest_path.open("wb") as f:
        tomli_w.dump(
            {
                "skills": {
                    "skill-a": {
                        "source": str(tmp_path / ".skills-repo" / "skills" / "skill-a"),
                        "version": "v2026.03.20",
                    },
                    "skill-b": {
                        "source": str(tmp_path / ".skills-repo" / "skills" / "skill-b"),
                        "version": "v2026.03.23",
                    },
                }
            },
            f,
        )

    return project


class TestStatusCommand:
    """Tests for status command."""

    def test_status_shows_installed_skills(
        self, cli_runner: CliRunner, project_with_skills: Path
    ) -> None:
        """Test status shows installed skills."""
        result = cli_runner.invoke(
            main,
            ["status", str(project_with_skills)],
        )

        assert result.exit_code == 0, result.output
        assert "skill-a" in result.output
        assert "skill-b" in result.output

    def test_status_empty_project(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test status with no skills installed."""
        project = tmp_path / "empty-project"
        project.mkdir()

        result = cli_runner.invoke(
            main,
            ["status", str(project)],
        )

        assert result.exit_code == 0, result.output
        assert "No skills installed" in result.output
