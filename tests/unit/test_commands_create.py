"""Tests for create command."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def initialized_repo(tmp_path: Path) -> Path:
    """Create an initialized repository."""
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

    return repo_path


class TestCreateCommand:
    """Tests for create command."""

    def test_create_new_skill(
        self, cli_runner: CliRunner, initialized_repo: Path
    ) -> None:
        """Test creating a new skill."""
        result = cli_runner.invoke(
            main,
            [
                "create",
                "my-skill",
                "--repo",
                str(initialized_repo),
                "--description",
                "A test skill",
            ],
        )

        assert result.exit_code == 0
        assert "Created skill 'my-skill'" in result.output

        skill_dir = initialized_repo / "skills" / "my-skill"
        expected_version = f"v{date.today().strftime('%Y.%m.%d')}"
        assert skill_dir.exists()
        assert (skill_dir / "skill.yaml").exists()
        assert (skill_dir / expected_version).exists()
        assert ((skill_dir / expected_version) / "SKILL.md").exists()

    def test_create_skill_with_yaml(
        self, cli_runner: CliRunner, initialized_repo: Path
    ) -> None:
        """Test skill.yaml is created correctly."""
        result = cli_runner.invoke(
            main,
            [
                "create",
                "code-review",
                "--repo",
                str(initialized_repo),
                "--description",
                "Code review skill",
            ],
        )

        assert result.exit_code == 0

        skill_yaml = initialized_repo / "skills" / "code-review" / "skill.yaml"
        assert skill_yaml.exists()

        content = skill_yaml.read_text()
        assert "name = 'code-review'" in content or 'name = "code-review"' in content

    def test_create_duplicate_skill(
        self, cli_runner: CliRunner, initialized_repo: Path
    ) -> None:
        """Test creating a skill that already exists."""
        # Create first skill
        cli_runner.invoke(
            main,
            ["create", "duplicate", "--repo", str(initialized_repo)],
        )

        # Try to create again
        result = cli_runner.invoke(
            main,
            ["create", "duplicate", "--repo", str(initialized_repo)],
        )

        assert "already exists" in result.output

    def test_create_in_nonexistent_repo(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test creating skill in non-initialized repo."""
        result = cli_runner.invoke(
            main,
            ["create", "test", "--repo", str(tmp_path / "nonexistent")],
        )

        output_lower = result.output.lower()
        assert "not initialized" in output_lower or "does not exist" in output_lower
