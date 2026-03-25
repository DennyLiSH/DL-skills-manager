"""Tests for init command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_repo_structure(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init creates correct directory structure."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(
                main, ["init", "--skills-path", str(tmp_path / "skills")]
            )

        assert result.exit_code == 0
        assert mock_config_path.exists()
        assert (mock_config_path / "config.toml").exists()

    def test_init_creates_config_file(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init creates config.toml with correct content."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(
                main, ["init", "--skills-path", str(tmp_path / "custom-skills")]
            )

        assert result.exit_code == 0
        config_path = mock_config_path / "config.toml"
        content = config_path.read_text()
        assert "[basic]" in content
        assert "[settings]" in content
        assert "skills_store" in content

    def test_init_already_exists(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test init fails when config dir already exists."""
        mock_config_path = tmp_path / ".skill-sync"
        mock_config_path.mkdir(parents=True, exist_ok=True)

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(main, ["init"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_init_default_skills_path(self, cli_runner: CliRunner) -> None:
        """Test init with --help shows default path option."""
        result = cli_runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--skills-path" in result.output
