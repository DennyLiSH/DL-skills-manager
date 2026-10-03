"""Unit tests for targets module (resolve + ensure)."""

from pathlib import Path

import pytest

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands.targets import (
    ensure_target_dir,
    resolve_command_target_dir,
)
from dl_skills_manager.core.exceptions import ValidationError


class TestResolveCommandTargetDir:
    """resolve is a pure query: it computes paths, creates nothing."""

    def test_global_returns_home_claude_skills(self, fake_home: Path) -> None:
        result = resolve_command_target_dir(is_global=True, project=".")
        assert result == fake_home / ".claude" / "skills"
        assert not result.exists()

    def test_local_returns_project_claude_skills(self, tmp_path: Path) -> None:
        project = tmp_path / "new-project"
        project.mkdir()
        result = resolve_command_target_dir(is_global=False, project=str(project))
        assert result == project / ".claude" / "skills"
        assert not result.exists()

    def test_agent_global(self, fake_home: Path) -> None:
        result = resolve_command_target_dir(is_global=True, project=".", agent="codex")
        assert result == fake_home / ".agents" / "skills"
        assert not result.exists()

    def test_agent_global_tilde_override(self, fake_home: Path) -> None:
        """'~'-prefixed override must land under the fake home.

        Path.home() is the documented home seam; this test asserts the
        resolved path lands under fake_home (fake_home also redirects
        the env vars, so this is a path-correctness pin rather than an
        implementation pin).
        """
        result = resolve_command_target_dir(
            is_global=True,
            project=".",
            agent="codex",
            agent_overrides={"codex": AgentDirOverride(global_dir="~/.codex/skills")},
        )
        assert result == fake_home / ".codex" / "skills"
        assert not result.exists()

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
        assert not result.exists()

    def test_agent_project(self, tmp_path: Path) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        result = resolve_command_target_dir(
            is_global=False, project=str(project), agent="pi"
        )
        assert result == project / ".pi" / "skills"
        assert not result.exists()

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


class TestEnsureTargetDir:
    """ensure_target_dir is the explicit 'ready to write' contract."""

    def test_creates_missing_dir(self, tmp_path: Path) -> None:
        target = tmp_path / "deep" / ".claude" / "skills"
        assert ensure_target_dir(target) == target
        assert target.is_dir()

    def test_idempotent_on_existing_dir(self, tmp_path: Path) -> None:
        target = tmp_path / "skills"
        target.mkdir()
        assert ensure_target_dir(target) == target
