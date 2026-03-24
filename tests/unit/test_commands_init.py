"""Tests for init command."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from dl_skills_manager.cli import main


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_repo_structure(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init creates correct directory structure."""
        repo_path = tmp_path / ".skills-repo"

        result = cli_runner.invoke(main, ["init", "--path", str(repo_path)])

        assert result.exit_code == 0
        assert repo_path.exists()
        assert (repo_path / "skills").exists()
        assert (repo_path / "templates").exists()
        assert (repo_path / "config.toml").exists()

    def test_init_creates_config_file(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init creates config.toml with correct content."""
        repo_path = tmp_path / ".skills-repo"

        result = cli_runner.invoke(main, ["init", "--path", str(repo_path)])

        assert result.exit_code == 0
        config_path = repo_path / "config.toml"
        content = config_path.read_text()
        assert "[repo]" in content
        assert "[settings]" in content

    def test_init_already_exists(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test init fails when repo already exists."""
        repo_path = tmp_path / ".skills-repo"
        repo_path.mkdir()

        result = cli_runner.invoke(main, ["init", "--path", str(repo_path)])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_default_path(self, cli_runner: CliRunner) -> None:
        """Test init with --help shows default path option."""
        result = cli_runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.output
