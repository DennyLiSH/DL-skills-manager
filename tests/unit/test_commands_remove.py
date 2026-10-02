"""Tests for remove command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands.remove import remove_skill
from dl_skills_manager.core.exceptions import ValidationError

if TYPE_CHECKING:
    from click.testing import CliRunner


def _install_skill(parent: Path, agent_subdir: str = ".claude") -> Path:
    """Create an installed skill dir under {parent}/{agent_subdir}/skills/."""
    skill = parent / agent_subdir / "skills" / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Test Skill\n")
    return skill


class TestRemoveSkillCore:
    """Core function tests: real config objects, no patches."""

    def test_removes_copy_from_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        skill = _install_skill(project)

        removed = remove_skill(
            "test-skill",
            is_global=False,
            project=str(project),
            agent="claude",
            config=mock_config(tmp_path),
        )

        assert removed is True
        assert not skill.exists()

    def test_not_installed_returns_false(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()

        removed = remove_skill(
            "nonexistent",
            is_global=False,
            project=str(project),
            agent="claude",
            config=mock_config(tmp_path),
        )

        assert removed is False

    def test_invalid_name_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="Invalid skill name"):
            remove_skill(
                "../evil",
                is_global=False,
                project=str(project),
                agent="claude",
                config=mock_config(tmp_path),
            )

    def test_removes_from_global(self, fake_home: Path) -> None:
        skill = _install_skill(fake_home)

        removed = remove_skill(
            "test-skill",
            is_global=True,
            project=".",
            agent="claude",
            config=mock_config(fake_home / "nowhere"),
        )

        assert removed is True
        assert not skill.exists()

    def test_removes_agent_global_codex(self, fake_home: Path) -> None:
        """--global × --agent codex combination (replaces the dropped
        legacy test_remove_agent_codex_global)."""
        skill = _install_skill(fake_home, ".agents")

        removed = remove_skill(
            "test-skill",
            is_global=True,
            project=".",
            agent="codex",
            config=mock_config(fake_home / "nowhere"),
        )

        assert removed is True
        assert not skill.exists()

    def test_agent_codex_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        skill = _install_skill(project, ".agents")

        removed = remove_skill(
            "test-skill",
            is_global=False,
            project=str(project),
            agent="codex",
            config=mock_config(tmp_path),
        )

        assert removed is True
        assert not skill.exists()

    def test_agent_uses_config_override(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        skill = _install_skill(project, ".codex")

        removed = remove_skill(
            "test-skill",
            is_global=False,
            project=str(project),
            agent="codex",
            config=mock_config(
                tmp_path,
                agent_dirs={"codex": AgentDirOverride(project_dir=".codex/skills")},
            ),
        )

        assert removed is True
        assert not skill.exists()

    def test_unknown_agent_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="Unknown agent"):
            remove_skill(
                "test-skill",
                is_global=False,
                project=str(project),
                agent="nope",
                config=mock_config(tmp_path),
            )

    def test_removes_symlink_preserving_target(self, tmp_path: Path) -> None:
        target_dir = tmp_path / "repo" / "skills" / "test-skill"
        target_dir.mkdir(parents=True)
        (target_dir / "SKILL.md").write_text("# Test Skill\n")

        project = tmp_path / "project"
        symlink = project / ".claude" / "skills" / "test-skill"
        symlink.parent.mkdir(parents=True)
        try:
            symlink.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        removed = remove_skill(
            "test-skill",
            is_global=False,
            project=str(project),
            agent="claude",
            config=mock_config(tmp_path),
        )

        assert removed is True
        assert not symlink.is_symlink()
        assert target_dir.exists()


class TestRemoveCli:
    """CLI adapter tests: real config via repo_home, no patches."""

    def test_cli_removes_from_project(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        skill = _install_skill(project)

        result = cli_runner.invoke(main, ["remove", "test-skill", str(project)])

        assert result.exit_code == 0, result.output
        assert "Removed test-skill from project." in result.output
        assert not skill.exists()

    def test_cli_not_installed_message(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(
            main, ["remove", "nonexistent-skill", str(project)]
        )

        assert "not installed" in result.output.lower()

    def test_cli_global(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        skill = _install_skill(repo_home.parent)

        result = cli_runner.invoke(main, ["remove", "--global", "test-skill"])

        assert result.exit_code == 0, result.output
        assert "Removed test-skill from global skills" in result.output
        assert not skill.exists()

    def test_cli_global_nonexistent(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        result = cli_runner.invoke(main, ["remove", "--global", "nonexistent"])
        assert "not installed in global skills" in result.output

    def test_cli_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """UsageError fires in the adapter before any config access."""
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(
            main, ["remove", "--global", "test-skill", str(project)]
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output

    def test_cli_requires_initialized_repo(
        self, cli_runner: CliRunner, fake_home: Path, tmp_path: Path
    ) -> None:
        """No config.toml under fake home -> real ConfigError (spec D6b)."""
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(main, ["remove", "test-skill", str(project)])

        assert result.exit_code != 0
        assert "Config file not found" in result.output

    def test_cli_help_documents_agent_and_init_requirement(
        self, cli_runner: CliRunner
    ) -> None:
        result = cli_runner.invoke(main, ["remove", "--help"])
        assert result.exit_code == 0
        assert "initialized skill-sync repository" in result.output
