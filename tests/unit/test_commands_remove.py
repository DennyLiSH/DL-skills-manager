"""Tests for remove command."""

import importlib
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main
from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.config import SkillSyncConfig
from dl_skills_manager.core.exceptions import ConfigError

if TYPE_CHECKING:
    from click.testing import CliRunner

# The package __init__ re-exports the click Command as ``remove``, shadowing
# the submodule in getattr chains. pytest's dotted-path resolution uses
# getattr and would patch the Command, not the module — resolve explicitly.
_REMOVE_MODULE = importlib.import_module("dl_skills_manager.core.commands.remove")


@pytest.fixture
def project_with_skill(tmp_path: Path) -> Path:
    """Create a project with an installed skill."""
    project = tmp_path / "my-project"
    project.mkdir()

    # Create .claude/skills directory and skill
    skill_dir = project / ".claude" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")

    # Create skills.toml manifest
    manifest_path = project / ".claude" / "skills.toml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    skill_source = tmp_path / ".skills-repo" / "skills" / "test-skill"
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

    return project


@pytest.fixture(autouse=True)
def _mock_remove_load_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate remove from the real ~/.skill-sync/config.toml.

    remove reads config for [agents] overrides (spec D6b). raising=False:
    remove.load_config only exists after Step 3 adds the import; before
    that this patch is a harmless no-op.
    """
    monkeypatch.setattr(
        _REMOVE_MODULE,
        "load_config",
        lambda: SkillSyncConfig(
            path=tmp_path / ".skill-sync",
            skills_store=tmp_path / "store",
            default_link_mode="copy",
        ),
        raising=False,
    )


class TestRemoveCommand:
    """Tests for remove command."""

    def test_remove_skill_from_project(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill from a project."""
        skill_link = project_with_skill / ".claude" / "skills" / "test-skill"
        assert skill_link.exists()

        result = cli_runner.invoke(
            main,
            ["remove", "test-skill", str(project_with_skill)],
        )

        assert result.exit_code == 0, result.output
        assert "Removed test-skill" in result.output

    def test_remove_nonexistent_skill(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill that isn't installed."""
        result = cli_runner.invoke(
            main,
            ["remove", "nonexistent-skill", str(project_with_skill)],
        )

        # Should still exit 0 but warn
        assert "not installed" in result.output.lower()

    def test_remove_invalid_name(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test removing a skill with path traversal in name."""
        result = cli_runner.invoke(
            main,
            ["remove", "../evil", str(project_with_skill)],
        )

        assert result.exit_code != 0

    def test_remove_global(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test removing a skill from global ~/.claude/skills/."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        global_skills = fake_home / ".claude" / "skills"
        skill_dir = global_skills / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\n")

        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = cli_runner.invoke(
                main,
                ["remove", "--global", "test-skill"],
            )

        assert result.exit_code == 0, result.output
        assert "Removed test-skill from global skills" in result.output
        assert not skill_dir.exists()

    def test_remove_global_nonexistent(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test removing a nonexistent global skill."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = cli_runner.invoke(
                main,
                ["remove", "--global", "nonexistent"],
            )

        assert "not installed in global skills" in result.output

    def test_remove_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, project_with_skill: Path
    ) -> None:
        """Test --global with explicit PROJECT path raises error."""
        result = cli_runner.invoke(
            main,
            ["remove", "--global", "test-skill", str(project_with_skill)],
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output

    def test_remove_agent_codex_project(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Remove a skill installed under <project>/.agents/skills/."""
        project = tmp_path / "proj"
        project.mkdir()
        skill_dir = project / ".agents" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# test\n")

        result = cli_runner.invoke(
            main,
            ["remove", "--agent", "codex", "test-skill", str(project)],
        )

        assert result.exit_code == 0, result.output
        assert not skill_dir.exists()

    def test_remove_unknown_agent_errors(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(
            main,
            ["remove", "--agent", "nope", "test-skill", str(project)],
        )

        assert result.exit_code != 0
        assert "Unknown agent" in result.output

    def test_remove_agent_codex_global(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Remove a skill installed under ~/.agents/skills/ (--global)."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        skill_dir = fake_home / ".agents" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = cli_runner.invoke(
                main,
                ["remove", "--global", "--agent", "codex", "test-skill"],
            )

        assert result.exit_code == 0, result.output
        assert not skill_dir.exists()

    def test_remove_requires_initialized_repo(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Behavior change (spec D6b): uninitialized repo → clear error."""
        project = tmp_path / "proj"
        project.mkdir()

        def _raise() -> SkillSyncConfig:
            raise ConfigError("Config file not found: ~/.skill-sync/config.toml")

        monkeypatch.setattr(_REMOVE_MODULE, "load_config", _raise)
        result = cli_runner.invoke(
            main,
            ["remove", "test-skill", str(project)],
        )

        assert result.exit_code != 0
        assert "Config file not found" in result.output

    def test_remove_agent_uses_config_override(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """[agents] override redirects remove target too."""
        monkeypatch.setattr(
            _REMOVE_MODULE,
            "load_config",
            lambda: SkillSyncConfig(
                path=tmp_path / ".skill-sync",
                skills_store=tmp_path / "store",
                default_link_mode="copy",
                agent_dirs={"codex": AgentDirOverride(project_dir=".codex/skills")},
            ),
        )
        project = tmp_path / "proj"
        project.mkdir()
        skill_dir = project / ".codex" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)

        result = cli_runner.invoke(
            main,
            ["remove", "--agent", "codex", "test-skill", str(project)],
        )

        assert result.exit_code == 0, result.output
        assert not skill_dir.exists()


class TestRemoveSymlink:
    """Tests for remove command symlink handling."""

    def test_remove_symlink_preserves_target(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test removing a symlink does not delete the target directory."""
        # Create the real target directory
        target_dir = tmp_path / "repo" / "skills" / "test-skill"
        target_dir.mkdir(parents=True)
        (target_dir / "SKILL.md").write_text("# Test Skill\n")

        # Create project and symlink
        project = tmp_path / "project"
        skills_dir = project / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        symlink_path = skills_dir / "test-skill"

        # Try to create symlink, skip test if not supported
        try:
            symlink_path.symlink_to(target_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        assert symlink_path.is_symlink()
        assert target_dir.exists()

        result = cli_runner.invoke(
            main,
            ["remove", "test-skill", str(project)],
        )

        assert result.exit_code == 0, result.output
        assert "Removed test-skill" in result.output

        # Symlink should be gone
        assert not symlink_path.exists()
        assert not symlink_path.is_symlink()

        # Target directory should be preserved
        assert target_dir.exists()
        assert (target_dir / "SKILL.md").exists()
