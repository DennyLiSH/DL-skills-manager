"""Tests for versions command."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from test_helpers import mock_config

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_versions(tmp_path: Path) -> Path:
    """Create a repository with multiple versions in .bk/."""
    repo_path = tmp_path / ".skill-sync"
    repo_path.mkdir()
    skills_dir = repo_path / "skills"
    skills_dir.mkdir()

    # Create config.toml
    config_path = repo_path / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(repo_path), "skills_store": str(skills_dir)},
                "settings": {"default_link_mode": "symlink"},
            },
            f,
        )

    # Create current skill
    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Current\n")

    # Create history versions in .bk/
    bk_dir = skills_dir / ".bk"
    bk_dir.mkdir()

    for version in ["v2026.03.20", "v2026.03.23", "v2026.03.25-dev"]:
        v_dir = bk_dir / f"test-skill@{version}"
        v_dir.mkdir()
        (v_dir / "SKILL.md").write_text(f"# {version}\n")

    return repo_path


class TestVersionsCommand:
    """Tests for versions command."""

    def test_versions_lists_all(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test listing all versions from .bk/."""
        with (
            patch(
                "dl_skills_manager.core.commands.versions.load_config",
                return_value=mock_config(repo_with_versions),
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_config(repo_with_versions),
            ),
        ):
            result = cli_runner.invoke(main, ["versions", "test-skill"])

        assert result.exit_code == 0, result.output
        assert "current" in result.output
        assert "v2026.03.20" in result.output
        assert "v2026.03.23" in result.output
        assert "v2026.03.25-dev" in result.output

    def test_versions_shows_current_marker(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test versions shows current marker."""
        with (
            patch(
                "dl_skills_manager.core.commands.versions.load_config",
                return_value=mock_config(repo_with_versions),
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_config(repo_with_versions),
            ),
        ):
            result = cli_runner.invoke(main, ["versions", "test-skill"])

        assert "current" in result.output

    def test_versions_nonexistent_skill(
        self, cli_runner: CliRunner, repo_with_versions: Path
    ) -> None:
        """Test versions for nonexistent skill."""
        with (
            patch(
                "dl_skills_manager.core.commands.versions.load_config",
                return_value=mock_config(repo_with_versions),
            ),
            patch(
                "dl_skills_manager.core.commands._shared.load_config",
                return_value=mock_config(repo_with_versions),
            ),
        ):
            result = cli_runner.invoke(main, ["versions", "nonexistent"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
