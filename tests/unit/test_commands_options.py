"""Tests for shared CLI target option decorators."""

import click
import pytest
from click.testing import CliRunner

from dl_skills_manager.core.commands._options import (
    reject_global_with_project,
    target_options,
)


@click.command()
@target_options()
def _sample(project: str, *, is_global: bool, agent: str) -> None:
    click.echo(f"{project}|{is_global}|{agent}")


class TestTargetOptions:
    """target_options attaches PROJECT/--global/--agent with defaults."""

    def test_defaults(self) -> None:
        result = CliRunner().invoke(_sample, [])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == ".|False|claude"

    def test_explicit_values(self) -> None:
        result = CliRunner().invoke(_sample, ["myproj", "--global", "--agent", "codex"])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == "myproj|True|codex"

    def test_custom_agent_help_shown(self) -> None:
        @click.command()
        @target_options(agent_help="Custom help text")
        def cmd(project: str, *, is_global: bool, agent: str) -> None:
            click.echo("ok")

        result = CliRunner().invoke(cmd, ["--help"])

        assert result.exit_code == 0, result.output
        assert "Custom help text" in result.output


class TestRejectGlobalWithProject:
    """Guard helper: --global and an explicit PROJECT are mutually exclusive."""

    def test_global_with_explicit_project_raises(self) -> None:
        with pytest.raises(click.UsageError, match="Cannot specify both"):
            reject_global_with_project(is_global=True, project="myproj")

    def test_global_with_default_project_ok(self) -> None:
        reject_global_with_project(is_global=True, project=".")

    def test_local_with_explicit_project_ok(self) -> None:
        reject_global_with_project(is_global=False, project="myproj")
