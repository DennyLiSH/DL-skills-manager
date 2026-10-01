"""Tests for agent registry and directory resolution."""

import pytest

from dl_skills_manager.core.agents import (
    BUILTIN_AGENTS,
    AgentDirOverride,
    AgentSpec,
    resolve_agent_dirs,
)
from dl_skills_manager.core.exceptions import ValidationError


class TestBuiltinAgents:
    """Tests for the built-in agent registry."""

    def test_contains_five_agents(self) -> None:
        assert set(BUILTIN_AGENTS) == {"claude", "codex", "pi", "zcode", "workbuddy"}

    def test_claude_layout(self) -> None:
        spec = BUILTIN_AGENTS["claude"]
        assert spec.global_dir == ".claude/skills"
        assert spec.project_dir == ".claude/skills"

    def test_codex_uses_agents_standard(self) -> None:
        spec = BUILTIN_AGENTS["codex"]
        assert spec.global_dir == ".agents/skills"
        assert spec.project_dir == ".agents/skills"

    def test_pi_layout(self) -> None:
        spec = BUILTIN_AGENTS["pi"]
        assert spec.global_dir == ".pi/agent/skills"
        assert spec.project_dir == ".pi/skills"

    def test_zcode_layout(self) -> None:
        spec = BUILTIN_AGENTS["zcode"]
        assert spec.global_dir == ".zcode/skills"
        assert spec.project_dir == ".zcode/skills"

    def test_workbuddy_layout(self) -> None:
        spec = BUILTIN_AGENTS["workbuddy"]
        assert spec.global_dir == ".workbuddy/skills"
        assert spec.project_dir is None


class TestBuiltinAgentsImmutable:
    """BUILTIN_AGENTS is a read-only mapping (MappingProxyType)."""

    def test_item_assignment_and_deletion_raise(self) -> None:
        with pytest.raises(TypeError):
            BUILTIN_AGENTS["new-agent"] = AgentSpec(
                global_dir="~/.new/skills", project_dir=None
            )
        with pytest.raises(TypeError):
            del BUILTIN_AGENTS["claude"]

    def test_snapshot_via_dict_copy_still_possible(self) -> None:
        snapshot = dict(BUILTIN_AGENTS)
        assert snapshot["claude"].global_dir == ".claude/skills"


class TestResolveAgentDirs:
    """Tests for resolve_agent_dirs merging and validation."""

    def test_builtin_without_overrides(self) -> None:
        assert resolve_agent_dirs("codex") == (".agents/skills", ".agents/skills")

    def test_override_replaces_only_global_dir(self) -> None:
        overrides = {"codex": AgentDirOverride(global_dir="~/.codex/skills")}
        result = resolve_agent_dirs("codex", overrides)
        assert result == ("~/.codex/skills", ".agents/skills")

    def test_override_replaces_only_project_dir(self) -> None:
        overrides = {"codex": AgentDirOverride(project_dir=".codex/skills")}
        result = resolve_agent_dirs("codex", overrides)
        assert result == (".agents/skills", ".codex/skills")

    def test_custom_agent_both_dirs(self) -> None:
        overrides = {
            "mytool": AgentDirOverride(
                global_dir="~/.mytool/skills", project_dir=".mytool/skills"
            )
        }
        result = resolve_agent_dirs("mytool", overrides)
        assert result == ("~/.mytool/skills", ".mytool/skills")

    def test_custom_agent_project_only(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir=".mytool/skills")}
        result = resolve_agent_dirs("mytool", overrides)
        assert result == (None, ".mytool/skills")

    def test_custom_agent_global_only(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~/.mytool/skills")}
        result = resolve_agent_dirs("mytool", overrides)
        assert result == ("~/.mytool/skills", None)

    def test_custom_agent_without_any_dir_raises(self) -> None:
        overrides = {"mytool": AgentDirOverride()}
        with pytest.raises(ValidationError, match="mytool"):
            resolve_agent_dirs("mytool", overrides)

    def test_unknown_agent_lists_available(self) -> None:
        with pytest.raises(ValidationError, match="claude, codex"):
            resolve_agent_dirs("nope")

    def test_unknown_agent_lists_config_defined(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~/.m/s")}
        with pytest.raises(ValidationError, match="mytool"):
            resolve_agent_dirs("nope", overrides)

    def test_invalid_project_dir_absolute(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir="/abs/skills")}
        with pytest.raises(ValidationError, match="relative path"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_project_dir_traversal(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir="../skills")}
        with pytest.raises(ValidationError, match="relative path"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_project_dir_drive_letter(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir="C:/skills")}
        with pytest.raises(ValidationError, match="relative path"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_project_dir_backslash_absolute(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir="\\abs\\skills")}
        with pytest.raises(ValidationError, match="relative path"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_project_dir_empty(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir="   ")}
        with pytest.raises(ValidationError, match="must not be empty"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_empty(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="  ")}
        with pytest.raises(ValidationError, match="global_dir must not be empty"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_bare_tilde(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~")}
        with pytest.raises(ValidationError, match="must start with '~/"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_tilde_without_slash(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~codex")}
        with pytest.raises(ValidationError, match="must start with '~/"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_relative_dotdot(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="../escape")}
        with pytest.raises(ValidationError, match="global_dir"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_drive_relative(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="C:skills")}
        with pytest.raises(ValidationError, match="global_dir"):
            resolve_agent_dirs("mytool", overrides)

    def test_invalid_global_dir_tilde_dotdot(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~/../escape")}
        with pytest.raises(ValidationError, match="global_dir"):
            resolve_agent_dirs("mytool", overrides)


class TestGlobalDirHardening:
    """Hardening cases for global_dir values (20261001 code review)."""

    def test_global_dir_bare_tilde_slash_rejected(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~/")}
        with pytest.raises(
            ValidationError, match="path under the home directory"
        ):
            resolve_agent_dirs("mytool", overrides)

    def test_global_dir_tilde_slashes_only_rejected(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~//")}
        with pytest.raises(
            ValidationError, match="path under the home directory"
        ):
            resolve_agent_dirs("mytool", overrides)

    def test_global_dir_surrounding_whitespace_rejected(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir=" ~/mytool/skills")}
        with pytest.raises(ValidationError, match="whitespace"):
            resolve_agent_dirs("mytool", overrides)
        overrides = {"mytool": AgentDirOverride(global_dir="~/ ")}
        with pytest.raises(ValidationError, match="whitespace"):
            resolve_agent_dirs("mytool", overrides)

    def test_global_dir_tilde_backslash_normalized(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="~\\.mytool\\skills")}
        assert resolve_agent_dirs("mytool", overrides) == ("~/.mytool/skills", None)

    def test_global_dir_relative_backslash_normalized(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="mytool\\skills")}
        assert resolve_agent_dirs("mytool", overrides) == ("mytool/skills", None)

    def test_global_dir_tilde_drive_segment_rejected(self) -> None:
        """'~/d:secret' / '~/c:..' reset Path.home() joins on Windows."""
        for bad in ("~/d:secret", "~/c:.."):
            overrides = {"mytool": AgentDirOverride(global_dir=bad)}
            with pytest.raises(ValidationError, match="':'"):
                resolve_agent_dirs("mytool", overrides)

    def test_global_dir_colon_segment_rejected(self) -> None:
        overrides = {"mytool": AgentDirOverride(global_dir="mytool/sk:ills")}
        with pytest.raises(ValidationError, match="':'"):
            resolve_agent_dirs("mytool", overrides)

    def test_global_dir_dot_segment_rejected(self) -> None:
        """'~/.' / '.' resolve to the home root — same effect as bare '~/'."""
        for bad in ("~/.", "~/foo/.", "."):
            overrides = {"mytool": AgentDirOverride(global_dir=bad)}
            with pytest.raises(ValidationError, match="must not contain"):
                resolve_agent_dirs("mytool", overrides)


class TestProjectDirNormalization:
    """project_dir values are returned in POSIX style (20261001 code review)."""

    def test_project_dir_backslash_normalized_custom_agent(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir=".mytool\\skills")}
        assert resolve_agent_dirs("mytool", overrides) == (None, ".mytool/skills")

    def test_project_dir_backslash_normalized_builtin_override(self) -> None:
        overrides = {"codex": AgentDirOverride(project_dir=".codex\\skills")}
        assert resolve_agent_dirs("codex", overrides) == (
            ".agents/skills",
            ".codex/skills",
        )

    def test_project_dir_colon_segment_rejected(self) -> None:
        """Colon segments are Windows-invalid names; fail early and clearly."""
        overrides = {"mytool": AgentDirOverride(project_dir=".mytool/sk:ills")}
        with pytest.raises(ValidationError, match="':'"):
            resolve_agent_dirs("mytool", overrides)

    def test_project_dir_surrounding_whitespace_rejected(self) -> None:
        overrides = {"mytool": AgentDirOverride(project_dir=" .mytool/skills")}
        with pytest.raises(ValidationError, match="whitespace"):
            resolve_agent_dirs("mytool", overrides)

    def test_project_dir_dot_segment_rejected(self) -> None:
        """'.' / './' resolve to the project root itself."""
        for bad in (".", "./"):
            overrides = {"mytool": AgentDirOverride(project_dir=bad)}
            with pytest.raises(ValidationError, match="relative path"):
                resolve_agent_dirs("mytool", overrides)
