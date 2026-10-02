"""Tests for list command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.list import list_skills

if TYPE_CHECKING:
    from click.testing import CliRunner


def _seed_skill_with_history(repo: Path) -> None:
    skill = repo / "data" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Test Skill\n")
    bk = repo / "data" / ".bk" / "test-skill@v2026.03.22"
    bk.mkdir(parents=True)
    (bk / "SKILL.md").write_text("# Test Skill Old\n")


class TestListSkillsCore:
    """Core function tests: real config objects, no patches."""

    def test_list_skills_empty(self, repo_home: Path) -> None:
        assert list_skills(mock_config(repo_home)) == []

    def test_list_skills_with_history(self, repo_home: Path) -> None:
        _seed_skill_with_history(repo_home)

        skills = list_skills(mock_config(repo_home))

        assert len(skills) == 1
        assert skills[0].name == "test-skill"
        assert skills[0].history == ("v2026.03.22",)


class TestListCommand:
    """CLI adapter tests: real config via repo_home/fake_home, no patches."""

    def test_list_no_repo(self, cli_runner: CliRunner, fake_home: Path) -> None:
        """No config.toml under the fake home → ConfigError, exit 1."""
        result = cli_runner.invoke(main, ["list"])
        assert result.exit_code == 1

    def test_list_with_skills(self, cli_runner: CliRunner, repo_home: Path) -> None:
        _seed_skill_with_history(repo_home)

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0, result.output
        assert "test-skill" in result.output
        assert "1 history" in result.output
