"""Tests for mtp command (core function + CLI adapter)."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.mtp import promote_skill
from dl_skills_manager.core.exceptions import SkillNotFoundError, ValidationError
from dl_skills_manager.core.store import Promotion

if TYPE_CHECKING:
    from click.testing import CliRunner


def _seed_dev_skill(repo: Path, text: str = "# My Skill\n") -> None:
    dev = repo / "data" / ".dev" / "my-skill"
    dev.mkdir(parents=True, exist_ok=True)
    (dev / "SKILL.md").write_text(text)


class TestPromoteSkillCore:
    """Core function tests: real config objects, no patches."""

    def test_promotes_to_production_with_backup(self, repo_home: Path) -> None:
        _seed_dev_skill(repo_home)

        result = promote_skill("my-skill", config=mock_config(repo_home))

        assert isinstance(result, Promotion)
        target = repo_home / "data" / "skills" / "my-skill"
        assert (target / "SKILL.md").read_text() == "# My Skill\n"
        assert result.target == target
        assert result.backup.parent == repo_home / "data" / ".bk"
        assert result.backup.name.startswith("my-skill@v")

    def test_dev_not_found_raises(self, repo_home: Path) -> None:
        with pytest.raises(SkillNotFoundError, match="not found"):
            promote_skill("nonexistent", config=mock_config(repo_home))

    def test_invalid_name_raises(self, repo_home: Path) -> None:
        with pytest.raises(ValidationError, match="Invalid skill name"):
            promote_skill("../evil", config=mock_config(repo_home))


class TestMtpCommand:
    """CLI adapter tests via repo_home (real load_config, zero patches)."""

    def test_mtp_copies_to_production(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        _seed_dev_skill(repo_home)

        result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output
        assert "Moved 'my-skill' to production" in result.output

        target = repo_home / "data" / "skills" / "my-skill"
        assert (target / "SKILL.md").read_text() == "# My Skill\n"

        bk_entries = list((repo_home / "data" / ".bk").iterdir())
        assert len(bk_entries) == 1
        assert bk_entries[0].name.startswith("my-skill@v")

    def test_mtp_overwrites_existing(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        _seed_dev_skill(repo_home)
        existing = repo_home / "data" / "skills" / "my-skill"
        existing.mkdir()
        (existing / "SKILL.md").write_text("# Old Version\n")

        result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output
        assert (existing / "SKILL.md").read_text() == "# My Skill\n"

    def test_mtp_version_format(self, cli_runner: CliRunner, repo_home: Path) -> None:
        _seed_dev_skill(repo_home)

        result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output
        version_name = next((repo_home / "data" / ".bk").iterdir()).name
        version_part = version_name.split("@", 1)[1]
        assert re.fullmatch(r"v\d{4}\.\d{2}\.\d{2}", version_part), (
            f"Version '{version_part}' doesn't match vYYYY.MM.DD"
        )

    def test_mtp_same_day_increments(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        _seed_dev_skill(repo_home)

        result1 = cli_runner.invoke(main, ["mtp", "my-skill"])
        assert result1.exit_code == 0, result1.output

        _seed_dev_skill(repo_home, text="# Updated Skill\n")
        result2 = cli_runner.invoke(main, ["mtp", "my-skill"])
        assert result2.exit_code == 0, result2.output

        bk_entries = sorted(e.name for e in (repo_home / "data" / ".bk").iterdir())
        assert len(bk_entries) == 2
        versions = [e.split("@", 1)[1] for e in bk_entries]
        assert any(v.endswith(".1") for v in versions), (
            f"Expected .1 suffix in {versions}"
        )

    def test_mtp_dev_not_found(self, cli_runner: CliRunner, repo_home: Path) -> None:
        result = cli_runner.invoke(main, ["mtp", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_mtp_invalid_name(self, cli_runner: CliRunner, repo_home: Path) -> None:
        result = cli_runner.invoke(main, ["mtp", "../evil"])

        assert result.exit_code != 0
