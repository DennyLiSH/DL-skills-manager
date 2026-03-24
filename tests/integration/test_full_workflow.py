"""Full workflow integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dl_skills_manager.cli import main


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


class TestWorkflow:
    """Test complete workflows."""

    def test_init_creates_structure(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that init creates correct directory structure."""
        repo_path = tmp_path / ".skills-repo"

        result = cli_runner.invoke(main, ["init", "--path", str(repo_path)])

        assert result.exit_code == 0
        assert (repo_path / "skills").exists()
        assert (repo_path / "templates").exists()
        assert (repo_path / "config.toml").exists()

    def test_create_and_list_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test create and list workflow in same repo."""
        repo_path = tmp_path / ".skills-repo"

        # Init
        result = cli_runner.invoke(main, ["init", "--path", str(repo_path)])
        assert result.exit_code == 0

        # Create
        result = cli_runner.invoke(
            main,
            [
                "create",
                "test-skill",
                "--repo",
                str(repo_path),
                "--description",
                "Test skill",
            ],
        )
        assert result.exit_code == 0
        assert "Created skill" in result.output

        # List
        result = cli_runner.invoke(main, ["list", "--repo", str(repo_path)])
        assert result.exit_code == 0
        assert "test-skill" in result.output
