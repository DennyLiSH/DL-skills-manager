"""Tests for CLI-level behavior (version option)."""

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


def _pyproject_version() -> str:
    with (Path(__file__).parents[2] / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)["project"]["version"]


class TestVersionOption:
    """Tests for the top-level --version flag."""

    def test_version_prints_pyproject_version(self, cli_runner: CliRunner) -> None:
        """--version exits 0 and reports the pyproject.toml version."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert result.output.strip() == f"skill-sync, version {_pyproject_version()}"
