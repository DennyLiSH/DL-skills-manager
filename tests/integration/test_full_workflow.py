"""Full workflow integration tests."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestWorkflow:
    """Test complete workflows."""

    def test_init_creates_structure(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that init creates correct directory structure."""
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
        assert (mock_config_path / "config.toml").exists()

    def test_create_and_list_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test create and list workflow - skipped since create is TBD."""
        pytest.skip("create command is TBD")
