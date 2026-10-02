"""Unit tests for resolve_command_target_dir (targets module)."""

from pathlib import Path

import pytest

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands.targets import resolve_command_target_dir
from dl_skills_manager.core.exceptions import ValidationError


class TestResolveCommandTargetDir:
    """Tests for the single target dir resolution entry point."""

    def test_global_returns_home_claude_skills(self, fake_home: Path) -> None:
        """Global flag resolves to ~/.claude/skills/."""
        result = resolve_command_target_dir(is_global=True, project=".")
        assert result == fake_home / ".claude" / "skills"
        assert result.exists()

    def test_local_returns_project_claude_skills(self, tmp_path: Path) -> None:
        """Local resolves to {project}/.claude/skills/ and creates it."""
        project = tmp_path / "new-project"
        project.mkdir()
        result = resolve_command_target_dir(is_global=False, project=str(project))
        assert result == project / ".claude" / "skills"
        assert result.exists()

    def test_agent_global(self, fake_home: Path) -> None:
        result = resolve_command_target_dir(is_global=True, project=".", agent="codex")
        assert result == fake_home / ".agents" / "skills"
        assert result.is_dir()

    def test_agent_global_tilde_override(self, fake_home: Path) -> None:
        """'~'-prefixed override must resolve via the Path.home seam.

        expanduser() reads USERPROFILE and would bypass the seam (and
        write to the real home) — this test pins the home-seam behavior
        (unchanged from the merged-away implementation).
        """
        result = resolve_command_target_dir(
            is_global=True,
            project=".",
            agent="codex",
            agent_overrides={"codex": AgentDirOverride(global_dir="~/.codex/skills")},
        )
        assert result == fake_home / ".codex" / "skills"
        assert result.is_dir()

    def test_agent_global_absolute_path_override(self, tmp_path: Path) -> None:
        """Non-'~' absolute override is used as-is (no home involved)."""
        abs_dir = tmp_path / "custom-abs" / "skills"
        result = resolve_command_target_dir(
            is_global=True,
            project=".",
            agent="codex",
            agent_overrides={"codex": AgentDirOverride(global_dir=str(abs_dir))},
        )
        assert result == abs_dir
        assert result.is_dir()

    def test_agent_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_command_target_dir(
            is_global=False, project=str(project), agent="pi"
        )
        assert result == project / ".pi" / "skills"
        assert result.is_dir()

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

    def test_workbuddy_project_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="--global"):
            resolve_command_target_dir(
                is_global=False, project=str(project), agent="workbuddy"
            )

    def test_unknown_agent_raises(self) -> None:
        with pytest.raises(ValidationError, match="Unknown agent"):
            resolve_command_target_dir(is_global=True, project=".", agent="nope")

    def test_custom_agent_global_only_project_raises(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        with pytest.raises(ValidationError, match="does not support"):
            resolve_command_target_dir(
                is_global=False,
                project=str(project),
                agent="mytool",
                agent_overrides={"mytool": AgentDirOverride(global_dir="~/.m/s")},
            )

    def test_custom_agent_project_only_global_raises(self) -> None:
        with pytest.raises(ValidationError, match="does not define a global"):
            resolve_command_target_dir(
                is_global=True,
                project=".",
                agent="mytool",
                agent_overrides={
                    "mytool": AgentDirOverride(project_dir=".mytool/skills")
                },
            )
