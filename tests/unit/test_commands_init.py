"""Tests for init command."""

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
                main,
                [
                    "init",
                    "--skills-path",
                    str(tmp_path / "skills"),
                    "--link-mode",
                    "copy",
                ],
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
                main,
                [
                    "init",
                    "--skills-path",
                    str(tmp_path / "custom-skills"),
                    "--link-mode",
                    "copy",
                ],
            )

        assert result.exit_code == 0
        config_path = mock_config_path / "config.toml"
        content = config_path.read_text()
        assert "[basic]" in content
        assert "[settings]" in content
        assert "skills_store" in content

    def test_init_already_exists(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test init fails when config.toml already exists."""
        mock_config_path = tmp_path / ".skill-sync"
        mock_config_path.mkdir(parents=True, exist_ok=True)
        (mock_config_path / "config.toml").write_text("[basic]\n")

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(main, ["init"])

        assert result.exit_code == 1
        assert "already initialized" in result.output

    def test_init_default_skills_path(self, cli_runner: CliRunner) -> None:
        """Test init with --help shows default path option."""
        result = cli_runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--skills-path" in result.output


class TestInitLinkMode:
    """Tests for init command link mode prompt behavior."""

    def test_init_prompts_when_link_mode_not_specified(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init prompts for link mode when --link-mode is not given."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            # Provide "copy" as input to the prompt
            result = cli_runner.invoke(
                main,
                ["init", "--skills-path", str(tmp_path / "skills")],
                input="copy\n",
            )

        assert result.exit_code == 0, result.output
        assert "Default installation mode" in result.output

    def test_init_accepts_default_copy_via_prompt(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test init prompt accepts default (copy) when user presses enter."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            # Empty input = accept default
            result = cli_runner.invoke(
                main,
                ["init", "--skills-path", str(tmp_path / "skills")],
                input="\n",
            )

        assert result.exit_code == 0, result.output
        # Verify config.toml has copy as default
        config_content = (mock_config_path / "config.toml").read_text()
        assert "copy" in config_content

    def test_init_link_mode_option_skips_prompt(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test --link-mode option skips the interactive prompt."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "init",
                    "--skills-path",
                    str(tmp_path / "skills"),
                    "--link-mode",
                    "symlink",
                ],
            )

        assert result.exit_code == 0, result.output
        # No prompt should appear in output
        assert "Default installation mode" not in result.output
        # Verify symlink was written to config
        config_content = (mock_config_path / "config.toml").read_text()
        assert "symlink" in config_content
