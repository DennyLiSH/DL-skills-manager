"""Tests for install command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands.install import install_skill
from dl_skills_manager.core.exceptions import (
    SkillNotFoundError,
    ValidationError,
    VersionNotFoundError,
)

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    """Repository with one production skill and an empty .bk."""
    repo_path = tmp_path / ".skill-sync"
    (repo_path / "data" / "skills").mkdir(parents=True)
    (repo_path / "data" / ".bk").mkdir()
    skill_dir = repo_path / "data" / "skills" / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Test Skill\n")
    return repo_path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    return project


def _install(
    repo: Path,
    *,
    name: str = "test-skill",
    version: str | None = None,
    is_global: bool = False,
    project: str = ".",
    link_mode: str | None = None,
    agent: str = "claude",
    agent_dirs: dict[str, AgentDirOverride] | None = None,
) -> Path:
    """Invoke the core with a real config built from tmp paths."""
    return install_skill(
        name,
        version=version,
        is_global=is_global,
        project=project,
        link_mode=link_mode,
        agent=agent,
        config=mock_config(repo, agent_dirs=agent_dirs),
    )


class TestInstallSkillCore:
    """Core function tests: real config objects, no patches."""

    def test_copy_mode_creates_directory(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        dest = _install(repo_with_skill, project=str(project_dir))
        assert dest == project_dir / ".claude" / "skills" / "test-skill"
        assert dest.is_dir()
        assert not dest.is_symlink()
        assert (dest / "SKILL.md").read_text() == "# Test Skill\n"

    def test_install_nonexistent_skill(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(SkillNotFoundError, match="not found in repository"):
            _install(repo_with_skill, name="nonexistent", project=str(project_dir))

    def test_install_with_version_from_bk(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        bk = repo_with_skill / "data" / ".bk" / "test-skill@v2026.03.22"
        bk.mkdir()
        (bk / "SKILL.md").write_text("# Old Version\n")

        dest = _install(
            repo_with_skill, version="v2026.03.22", project=str(project_dir)
        )

        assert (dest / "SKILL.md").read_text() == "# Old Version\n"

    def test_install_nonexistent_version(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(VersionNotFoundError, match="not found for skill"):
            _install(repo_with_skill, version="v2099.99.99", project=str(project_dir))

    def test_install_overwrites_existing_copy(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        existing = project_dir / ".claude" / "skills" / "test-skill"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("# Old\n")

        _install(repo_with_skill, project=str(project_dir))

        assert (existing / "SKILL.md").read_text() == "# Test Skill\n"

    def test_install_global(self, repo_with_skill: Path, fake_home: Path) -> None:
        dest = _install(repo_with_skill, is_global=True)
        assert dest == fake_home / ".claude" / "skills" / "test-skill"
        assert dest.exists()

    def test_install_agent_codex_global(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        dest = _install(repo_with_skill, is_global=True, agent="codex")
        assert dest == fake_home / ".agents" / "skills" / "test-skill"

    def test_install_agent_pi_project(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        dest = _install(repo_with_skill, project=str(project_dir), agent="pi")
        assert dest == project_dir / ".pi" / "skills" / "test-skill"

    def test_install_agent_uses_config_override(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        dest = _install(
            repo_with_skill,
            is_global=True,
            agent="codex",
            agent_dirs={"codex": AgentDirOverride(global_dir="~/.codex/skills")},
        )
        assert dest == fake_home / ".codex" / "skills" / "test-skill"

    def test_install_agent_zcode_global(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        dest = _install(repo_with_skill, is_global=True, agent="zcode")
        assert dest == fake_home / ".zcode" / "skills" / "test-skill"

    def test_install_agent_workbuddy_global(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        dest = _install(repo_with_skill, is_global=True, agent="workbuddy")
        assert dest == fake_home / ".workbuddy" / "skills" / "test-skill"

    def test_install_custom_agent_from_config(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        dest = _install(
            repo_with_skill,
            is_global=True,
            agent="mytool",
            agent_dirs={"mytool": AgentDirOverride(global_dir="~/.mytool/skills")},
        )
        assert dest == fake_home / ".mytool" / "skills" / "test-skill"

    def test_install_workbuddy_project_errors(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(ValidationError, match="--global"):
            _install(repo_with_skill, project=str(project_dir), agent="workbuddy")

    def test_install_unknown_agent_errors(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(ValidationError, match="Unknown agent"):
            _install(repo_with_skill, project=str(project_dir), agent="nope")

    def test_install_rejects_bare_tilde_slash_global_dir(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        with pytest.raises(ValidationError, match="path under the home directory"):
            _install(
                repo_with_skill,
                is_global=True,
                agent="mytool",
                agent_dirs={"mytool": AgentDirOverride(global_dir="~/")},
            )
        assert not (fake_home / "test-skill").exists()

    def test_install_ignores_config_default_link_mode_symlink(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """install must NOT honor config.default_link_mode; copy is always the default.

        Regression guard: the only test preventing install from re-reading
        config.default_link_mode (ADR 0001). Do not delete or weaken.
        Real-filesystem assertion — no create_link mocking involved.
        """
        config = mock_config(repo_with_skill, default_link_mode="symlink")
        dest = install_skill(
            "test-skill",
            version=None,
            is_global=False,
            project=str(project_dir),
            link_mode=None,
            agent="claude",
            config=config,
        )
        assert dest.is_dir()
        assert not dest.is_symlink()

    def test_install_link_mode_symlink_override(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        """--link-mode symlink routes to create_link (symlink or Windows
        copy fallback — both prove the symlink branch was taken)."""
        dest = _install(repo_with_skill, project=str(project_dir), link_mode="symlink")
        assert (dest / "SKILL.md").read_text() == "# Test Skill\n"

    def test_install_link_mode_copy_override_replaces_symlink_config(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        existing = project_dir / ".claude" / "skills" / "test-skill"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("# Old Version\n")

        config = mock_config(repo_with_skill, default_link_mode="symlink")
        dest = install_skill(
            "test-skill",
            version=None,
            is_global=False,
            project=str(project_dir),
            link_mode="copy",
            agent="claude",
            config=config,
        )

        assert (dest / "SKILL.md").read_text() == "# Test Skill\n"
        assert dest.is_dir()
        assert not dest.is_symlink()


class TestInstallCli:
    """CLI adapter tests: real config via repo_home, no patches."""

    def test_cli_install_to_project(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        skill = repo_home / "data" / "skills" / "test-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# Test Skill\n")

        result = cli_runner.invoke(main, ["install", "test-skill", str(project)])

        assert result.exit_code == 0, result.output
        assert "Installed test-skill@latest" in result.output
        assert (project / ".claude" / "skills" / "test-skill").exists()

    def test_cli_install_with_version(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()
        skill = repo_home / "data" / "skills" / "test-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# Test Skill\n")
        bk = repo_home / "data" / ".bk" / "test-skill@v2026.03.22"
        bk.mkdir()
        (bk / "SKILL.md").write_text("# Old Version\n")

        result = cli_runner.invoke(
            main, ["install", "test-skill@v2026.03.22", str(project)]
        )

        assert result.exit_code == 0, result.output
        assert "v2026.03.22" in result.output
        installed = project / ".claude" / "skills" / "test-skill" / "SKILL.md"
        assert installed.read_text() == "# Old Version\n"

    def test_cli_install_global(self, cli_runner: CliRunner, repo_home: Path) -> None:
        skill = repo_home / "data" / "skills" / "test-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# Test Skill\n")

        result = cli_runner.invoke(main, ["install", "--global", "test-skill"])

        assert result.exit_code == 0, result.output
        assert "Installed test-skill@latest" in result.output
        assert (repo_home.parent / ".claude" / "skills" / "test-skill").exists()

    def test_cli_install_nonexistent_skill(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(main, ["install", "nonexistent", str(project)])

        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_cli_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """UsageError fires in the adapter before any config access."""
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(
            main, ["install", "--global", "test-skill", str(project)]
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output
