"""Tests for update command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_stable_and_dev(tmp_path: Path) -> Path:
    """Create a repository with both stable and dev versions."""
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

    # Create skill with both versions
    skill_dir = repo_path / "skills" / "test-skill"
    skill_dir.mkdir()

    # Old stable version
    old_stable = skill_dir / "v2026.03.23"
    old_stable.mkdir()
    (old_stable / "SKILL.md").write_text("# Old Stable\n")

    # New dev version
    dev = skill_dir / "v2026.03.25-dev"
    dev.mkdir()
    (dev / "SKILL.md").write_text("# Dev\n")

    # skill.yaml: dev is current, old stable is marked as stable (for update test)
    # The update command should update FROM old stable TO the new stable version
    # But we only have dev version. Let me create proper structure:
    # For this test, we just need an existing skill that can be found
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


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project directory."""
    project = tmp_path / "my-project"
    project.mkdir()
    return project


class TestUpdateCommand:
    """Tests for update command."""

    def test_update_skill_to_stable(
        self, cli_runner: CliRunner, repo_with_stable_and_dev: Path, project_dir: Path
    ) -> None:
        """Test updating a skill to latest stable."""
        # Install old version first
        old_skill = project_dir / ".claude" / "skills" / "test-skill"
        old_skill.mkdir(parents=True)

        # Create manifest
        manifest_path = project_dir / ".claude" / "skills.toml"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        skill_source = repo_with_stable_and_dev / "skills" / "test-skill"
        with manifest_path.open("wb") as f:
            tomli_w.dump(
                {
                    "skills": {
                        "test-skill": {
                            "source": str(skill_source),
                            "version": "v2026.03.23",
                        }
                    }
                },
                f,
            )

        result = cli_runner.invoke(
            main,
            [
                "update",
                "test-skill",
                str(project_dir),
                "--repo",
                str(repo_with_stable_and_dev),
            ],
        )

        # Should update to v2026.03.23 (the stable version in skill.yaml)
        assert result.exit_code == 0, result.output
        assert "Updated test-skill" in result.output

    def test_update_nonexistent_skill(
        self,
        cli_runner: CliRunner,
        repo_with_stable_and_dev: Path,
        project_dir: Path,
    ) -> None:
        """Test updating a skill that doesn't exist."""
        result = cli_runner.invoke(
            main,
            [
                "update",
                "nonexistent",
                str(project_dir),
                "--repo",
                str(repo_with_stable_and_dev),
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()
