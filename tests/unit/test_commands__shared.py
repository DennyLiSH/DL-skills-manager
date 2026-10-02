"""Unit tests for target dir resolution."""

from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands._shared import (
    resolve_command_target_dir,
    resolve_skills_target_dir,
)
from dl_skills_manager.core.exceptions import ValidationError


class TestResolveSkillsTargetDir:
    """Tests for resolve_skills_target_dir function."""

    def test_global_returns_home_claude_skills(self, tmp_path: Path) -> None:
        """Test global flag resolves to ~/.claude/skills/."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = resolve_skills_target_dir(global_flag=True)

        assert result == fake_home / ".claude" / "skills"
        assert result.exists()

    def test_local_returns_project_claude_skills(self, tmp_path: Path) -> None:
        """Test local resolves to {project}/.claude/skills/."""
        project = tmp_path / "my-project"
        project.mkdir()

        result = resolve_skills_target_dir(global_flag=False, project_path=project)

        assert result == project / ".claude" / "skills"
        assert result.exists()

    def test_local_without_project_path_raises(self) -> None:
        """Test error when local but no project_path provided."""
        with pytest.raises(ValidationError, match="project_path required"):
            resolve_skills_target_dir(global_flag=False)

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        """Test that the target directory is created when missing."""
        project = tmp_path / "new-project"
        project.mkdir()
        assert not (project / ".claude" / "skills").exists()

        result = resolve_skills_target_dir(global_flag=False, project_path=project)

        assert result.exists()


class TestResolveSkillsTargetDirAgent:
    """Tests for agent-aware target directory resolution."""

    def test_agent_global(self, tmp_path: Path) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = resolve_skills_target_dir(global_flag=True, agent="codex")
        assert result == fake_home / ".agents" / "skills"
        assert result.is_dir()

    def test_agent_global_tilde_override(self, tmp_path: Path) -> None:
        """'~'-prefixed override must resolve via the patched Path.home seam.

        expanduser() reads USERPROFILE and would bypass the seam (and write
        to the real home) — this test pins the corrected behavior.
        """
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = resolve_skills_target_dir(
                global_flag=True,
                agent="codex",
                agent_overrides={
                    "codex": AgentDirOverride(global_dir="~/.codex/skills")
                },
            )
        assert result == fake_home / ".codex" / "skills"
        assert result.is_dir()

    def test_agent_global_absolute_path_override(self, tmp_path: Path) -> None:
        """Non-'~' absolute override is used as-is (no home involved)."""
        abs_dir = tmp_path / "custom-abs" / "skills"
        result = resolve_skills_target_dir(
            global_flag=True,
            agent="codex",
            agent_overrides={"codex": AgentDirOverride(global_dir=str(abs_dir))},
        )
        assert result == abs_dir
        assert result.is_dir()

    def test_agent_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_skills_target_dir(
            global_flag=False, project_path=project, agent="pi"
        )
        assert result == project / ".pi" / "skills"
        assert result.is_dir()

    def test_default_agent_is_claude(self, tmp_path: Path) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = resolve_skills_target_dir(global_flag=True)
        assert result == fake_home / ".claude" / "skills"

    def test_workbuddy_project_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="--global"):
            resolve_skills_target_dir(
                global_flag=False, project_path=project, agent="workbuddy"
            )

    def test_unknown_agent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="Unknown agent"):
            resolve_skills_target_dir(global_flag=True, agent="nope")

    def test_custom_agent_global_only_project_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="does not support"):
            resolve_skills_target_dir(
                global_flag=False,
                project_path=project,
                agent="mytool",
                agent_overrides={"mytool": AgentDirOverride(global_dir="~/.m/s")},
            )

    def test_custom_agent_project_only_global_raises(self) -> None:
        with pytest.raises(ValidationError, match="does not define a global"):
            resolve_skills_target_dir(
                global_flag=True,
                agent="mytool",
                agent_overrides={
                    "mytool": AgentDirOverride(project_dir=".mytool/skills")
                },
            )


class TestResolveCommandTargetDir:
    """Tests for the command-level target dir helper."""

    def test_global_resolves_via_home(self, tmp_path: Path) -> None:
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch(
            "dl_skills_manager.core.commands._shared.Path.home",
            return_value=fake_home,
        ):
            result = resolve_command_target_dir(
                is_global=True, project=".", agent="codex"
            )
        assert result == fake_home / ".agents" / "skills"

    def test_project_resolves_project_string(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_command_target_dir(
            is_global=False, project=str(project), agent="pi"
        )
        assert result == project / ".pi" / "skills"

    def test_default_agent_is_claude(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_command_target_dir(is_global=False, project=str(project))
        assert result == project / ".claude" / "skills"

    def test_agent_overrides_passthrough(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_command_target_dir(
            is_global=False,
            project=str(project),
            agent="codex",
            agent_overrides={"codex": AgentDirOverride(project_dir=".codex/skills")},
        )
        assert result == project / ".codex" / "skills"
