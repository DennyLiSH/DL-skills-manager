"""Tests for versions command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.versions import list_versions
from dl_skills_manager.core.exceptions import SkillNotFoundError

if TYPE_CHECKING:
    from click.testing import CliRunner


def _seed_versioned_skill(repo: Path) -> None:
    """Seed data/skills/test-skill plus three backups in data/.bk/."""
    skill = repo / "data" / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Current\n")
    bk = repo / "data" / ".bk"
    for version in ["v2026.03.20", "v2026.03.23", "v2026.03.25-dev"]:
        v_dir = bk / f"test-skill@{version}"
        v_dir.mkdir()
        (v_dir / "SKILL.md").write_text(f"# {version}\n")


class TestListVersionsCore:
    """Core function tests: real config objects, no patches."""

    def test_returns_history_newest_first(self, repo_home: Path) -> None:
        _seed_versioned_skill(repo_home)

        versions = list_versions("test-skill", config=mock_config(repo_home))

        assert versions == ["v2026.03.25-dev", "v2026.03.23", "v2026.03.20"]

    def test_skill_without_backups_returns_empty(self, repo_home: Path) -> None:
        skill = repo_home / "data" / "skills" / "solo"
        skill.mkdir()
        (skill / "SKILL.md").write_text("#\n")

        assert list_versions("solo", config=mock_config(repo_home)) == []

    def test_missing_skill_raises(self, repo_home: Path) -> None:
        with pytest.raises(SkillNotFoundError, match="not found"):
            list_versions("nonexistent", config=mock_config(repo_home))


class TestVersionsCommand:
    """CLI adapter tests via repo_home (real load_config, zero patches)."""

    def test_versions_lists_all(self, cli_runner: CliRunner, repo_home: Path) -> None:
        _seed_versioned_skill(repo_home)

        result = cli_runner.invoke(main, ["versions", "test-skill"])

        assert result.exit_code == 0, result.output
        assert "current" in result.output
        assert "v2026.03.20" in result.output
        assert "v2026.03.23" in result.output
        assert "v2026.03.25-dev" in result.output

    def test_versions_nonexistent_skill(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        result = cli_runner.invoke(main, ["versions", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
