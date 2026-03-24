"""Tests for verify command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_dev_version(tmp_path: Path) -> Path:
    """Create a repository with a dev version ready to verify."""
    repo_path = tmp_path / ".skills-repo"
    repo_path.mkdir()
    (repo_path / "skills").mkdir()
    (repo_path / "templates").mkdir()

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "repo": {"name": "test", "path": str(repo_path)},
                "settings": {"default_link_mode": "symlink", "fallback_to_copy": True},
            },
            f,
        )

    # Create skill with dev version
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()

    # Stable version
    stable = skill_dir / "v2026.03.23"
    stable.mkdir()
    (stable / "SKILL.md").write_text("# Stable\n")

    # Dev version
    dev = skill_dir / "v2026.03.25-dev"
    dev.mkdir()
    (dev / "SKILL.md").write_text("# Dev\n")

    # skill.yaml points dev as current but stable is old
    skill_yaml = skill_dir / "skill.yaml"
    with skill_yaml.open("wb") as f:
        tomli_w.dump(
            {
                "name": "test-skill",
                "description": "A test skill",
                "version": "v2026.03.25-dev",
                "stable_version": "v2026.03.23",
            },
            f,
        )

    return repo_path


class TestVerifyCommand:
    """Tests for verify command."""

    def test_verify_promotes_dev_to_stable(
        self, cli_runner: CliRunner, repo_with_dev_version: Path
    ) -> None:
        """Test promoting a dev version to stable."""
        result = cli_runner.invoke(
            main,
            ["verify", "test-skill", "--repo", str(repo_with_dev_version)],
        )

        assert result.exit_code == 0, result.output
        assert "Promoted" in result.output

        skill_dir = repo_with_dev_version / "skills" / "test-skill"

        # Should now have v2026.03.25 as stable
        assert (skill_dir / "v2026.03.25").exists()
        assert not (skill_dir / "v2026.03.25-dev").exists()

    def test_verify_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_dev_version: Path
    ) -> None:
        """Test verifying a skill that doesn't exist."""
        result = cli_runner.invoke(
            main,
            ["verify", "nonexistent", "--repo", str(repo_with_dev_version)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
