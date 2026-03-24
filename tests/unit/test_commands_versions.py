"""Tests for versions command."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w
from click.testing import CliRunner

from dl_skills_manager.cli import main


@pytest.fixture
def repo_with_versions(tmp_path: Path) -> Path:
    """Create a repository with multiple versions."""
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

    # Create skill with multiple versions
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()

    # Version 1
    v1 = skill_dir / "v2026.03.20"
    v1.mkdir()
    (v1 / "SKILL.md").write_text("# V1\n")

    # Version 2 (stable)
    v2 = skill_dir / "v2026.03.23"
    v2.mkdir()
    (v2 / "SKILL.md").write_text("# V2\n")

    # Version 3 (dev, current)
    v3 = skill_dir / "v2026.03.25-dev"
    v3.mkdir()
    (v3 / "SKILL.md").write_text("# V3 Dev\n")

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


class TestVersionsCommand:
    """Tests for versions command."""

    def test_versions_lists_all(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test listing all versions."""
        result = cli_runner.invoke(
            main,
            ["versions", "test-skill", "--repo", str(repo_with_versions)],
        )

        assert result.exit_code == 0, result.output
        assert "v2026.03.20" in result.output
        assert "v2026.03.23" in result.output
        assert "v2026.03.25-dev" in result.output

    def test_versions_shows_markers(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test versions shows stable and current markers."""
        result = cli_runner.invoke(
            main,
            ["versions", "test-skill", "--repo", str(repo_with_versions)],
        )

        assert "stable" in result.output
        assert "current" in result.output

    def test_versions_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test versions for nonexistent skill."""
        result = cli_runner.invoke(
            main,
            ["versions", "nonexistent", "--repo", str(repo_with_versions)],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
