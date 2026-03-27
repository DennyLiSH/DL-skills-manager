"""Tests for mtp command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from dl_skills_manager.core.config import SkillSyncConfig

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_dev_skill(tmp_path: Path) -> Path:
    """Create a repository with a skill in .dev/."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    skills_dir = repo_path / "skills"
    skills_dir.mkdir()
    (skills_dir / ".bk").mkdir()

    # Create .dev/skill
    dev_dir = skills_dir / ".dev" / "my-skill"
    dev_dir.mkdir(parents=True)
    (dev_dir / "SKILL.md").write_text("# My Skill\n")

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {
                    "path": str(repo_path),
                    "skills_store": str(skills_dir),
                },
                "settings": {"default_link_mode": "copy"},
            },
            f,
        )

    return repo_path


def _mock_config(repo_path: Path) -> SkillSyncConfig:
    return SkillSyncConfig(
        path=repo_path,
        skills_store=repo_path / "skills",
        default_link_mode="copy",
    )


class TestMtpCommand:
    """Tests for mtp command."""

    def test_mtp_copies_to_production(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test mtp copies .dev skill to skills_store root."""
        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output
        assert "Moved 'my-skill' to production" in result.output

        # Verify skill exists at root
        target = repo_with_dev_skill / "skills" / "my-skill"
        assert target.exists()
        assert (target / "SKILL.md").read_text() == "# My Skill\n"

        # Verify backup exists in .bk
        bk_dir = repo_with_dev_skill / "skills" / ".bk"
        bk_entries = list(bk_dir.iterdir())
        assert len(bk_entries) == 1
        assert bk_entries[0].name.startswith("my-skill@v")

    def test_mtp_overwrites_existing(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test mtp overwrites existing skill in skills_store."""
        skills_store = repo_with_dev_skill / "skills"

        # Create existing skill at root (old version)
        existing = skills_store / "my-skill"
        existing.mkdir()
        (existing / "SKILL.md").write_text("# Old Version\n")

        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output

        # Verify old version was replaced
        assert (existing / "SKILL.md").read_text() == "# My Skill\n"

    def test_mtp_version_format(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test .bk version follows vYYYY.MM.DD format."""
        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            result = cli_runner.invoke(main, ["mtp", "my-skill"])

        assert result.exit_code == 0, result.output

        bk_dir = repo_with_dev_skill / "skills" / ".bk"
        bk_entries = list(bk_dir.iterdir())
        version_name = bk_entries[0].name

        # Should be my-skill@vYYYY.MM.DD
        assert version_name.startswith("my-skill@v")
        # Verify format matches vYYYY.MM.DD
        version_part = version_name.split("@", 1)[1]
        import re

        assert re.match(r"v\d{4}\.\d{2}\.\d{2}$", version_part), (
            f"Version '{version_part}' doesn't match vYYYY.MM.DD"
        )

    def test_mtp_same_day_increments(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test same-day mtp increments version suffix."""
        bk_dir = repo_with_dev_skill / "skills" / ".bk"

        # Create existing backup with same base version
        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            # First mtp
            result1 = cli_runner.invoke(main, ["mtp", "my-skill"])
            assert result1.exit_code == 0, result1.output

            # Re-create .dev skill for second mtp
            dev_dir = repo_with_dev_skill / "skills" / ".dev" / "my-skill"
            dev_dir.mkdir(parents=True, exist_ok=True)
            (dev_dir / "SKILL.md").write_text("# Updated Skill\n")

            # Second mtp (same day)
            result2 = cli_runner.invoke(main, ["mtp", "my-skill"])
            assert result2.exit_code == 0, result2.output

        # Should have two backups: base and .1
        bk_entries = sorted(e.name for e in bk_dir.iterdir())
        assert len(bk_entries) == 2
        # One should have .1 suffix
        versions = [e.split("@", 1)[1] for e in bk_entries]
        assert any(v.endswith(".1") for v in versions), (
            f"Expected .1 suffix in {versions}"
        )

    def test_mtp_dev_not_found(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test mtp fails when skill not in .dev/."""
        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            result = cli_runner.invoke(main, ["mtp", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_mtp_invalid_name(
        self, cli_runner: CliRunner, repo_with_dev_skill: Path
    ) -> None:
        """Test mtp fails with invalid skill name."""
        with patch(
            "dl_skills_manager.core.commands.mtp.load_config",
            return_value=_mock_config(repo_with_dev_skill),
        ):
            result = cli_runner.invoke(main, ["mtp", "../evil"])

        assert result.exit_code != 0
