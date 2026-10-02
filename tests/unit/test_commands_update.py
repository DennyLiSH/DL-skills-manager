"""Tests for update command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from test_helpers import mock_config

from dl_skills_manager.cli import main
from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.commands.update import update_skill
from dl_skills_manager.core.exceptions import SkillNotFoundError, ValidationError

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def repo_with_skill(tmp_path: Path) -> Path:
    repo_path = tmp_path / ".skill-sync"
    (repo_path / "data" / "skills" / "test-skill").mkdir(parents=True)
    (repo_path / "data" / "skills" / "test-skill" / "SKILL.md").write_text(
        "# Test Skill\n"
    )
    (repo_path / "data" / ".bk").mkdir()
    return repo_path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    return project


def _update(
    repo: Path,
    *,
    name: str = "test-skill",
    is_global: bool = False,
    project: str = ".",
    agent: str = "claude",
    agent_dirs: dict[str, AgentDirOverride] | None = None,
):
    return update_skill(
        name,
        is_global=is_global,
        project=project,
        agent=agent,
        config=mock_config(repo, agent_dirs=agent_dirs),
    )


def _install_old_copy(parent: Path, subdir: str = ".claude") -> Path:
    old = parent / subdir / "skills" / "test-skill"
    old.mkdir(parents=True)
    (old / "SKILL.md").write_text("# Old Version\n")
    return old


def _install_symlink(repo: Path, parent: Path, subdir: str = ".claude") -> Path:
    """Real symlink into the repo skill dir; skips when unsupported."""
    skills = parent / subdir / "skills"
    skills.mkdir(parents=True)
    link = skills / "test-skill"
    try:
        link.symlink_to(repo / "data" / "skills" / "test-skill")
    except OSError:
        pytest.skip("Symlinks not supported on this platform")
    return link


def _seed_skill(repo: Path) -> None:
    """Ensure the repo has test-skill (update resolves it before the
    symlink check)."""
    skill = repo / "data" / "skills" / "test-skill"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("# Test Skill\n")


class TestUpdateSkillCore:
    def test_updates_copy_install(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        old = _install_old_copy(project_dir)

        outcome = _update(repo_with_skill, project=str(project_dir))

        assert outcome.skipped is False
        assert outcome.path == old
        assert (old / "SKILL.md").read_text() == "# Test Skill\n"

    def test_updates_when_not_yet_installed(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        outcome = _update(repo_with_skill, project=str(project_dir))
        assert outcome.skipped is False
        assert (outcome.path / "SKILL.md").read_text() == "# Test Skill\n"

    def test_updates_global(self, repo_with_skill: Path, fake_home: Path) -> None:
        old = _install_old_copy(fake_home)

        outcome = _update(repo_with_skill, is_global=True)

        assert outcome.skipped is False
        assert (old / "SKILL.md").read_text() == "# Test Skill\n"

    def test_nonexistent_skill_raises(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(SkillNotFoundError, match="not found in repository"):
            _update(repo_with_skill, name="nonexistent", project=str(project_dir))

    def test_symlink_install_skips(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        link = _install_symlink(repo_with_skill, project_dir)

        outcome = _update(repo_with_skill, project=str(project_dir))

        assert outcome.skipped is True
        assert (
            outcome.symlink_target
            == (repo_with_skill / "data" / "skills" / "test-skill").resolve()
        )
        assert link.is_symlink()

    def test_agent_pi_project_recopies(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        old = _install_old_copy(project_dir, ".pi")

        outcome = _update(repo_with_skill, project=str(project_dir), agent="pi")

        assert outcome.skipped is False
        assert (old / "SKILL.md").read_text() == "# Test Skill\n"

    def test_agent_uses_config_override(
        self, repo_with_skill: Path, fake_home: Path
    ) -> None:
        old = _install_old_copy(fake_home, ".codex")

        outcome = _update(
            repo_with_skill,
            is_global=True,
            agent="codex",
            agent_dirs={"codex": AgentDirOverride(global_dir="~/.codex/skills")},
        )

        assert outcome.skipped is False
        assert (old / "SKILL.md").read_text() == "# Test Skill\n"

    def test_workbuddy_project_errors(
        self, repo_with_skill: Path, project_dir: Path
    ) -> None:
        with pytest.raises(ValidationError, match="--global"):
            _update(repo_with_skill, project=str(project_dir), agent="workbuddy")


class TestUpdateCli:
    def test_cli_updates_copy(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        _seed_skill(repo_home)
        project = tmp_path / "proj"
        old = _install_old_copy(project)

        result = cli_runner.invoke(main, ["update", "test-skill", str(project)])

        assert result.exit_code == 0, result.output
        assert "Updated test-skill to latest" in result.output
        assert (old / "SKILL.md").read_text() == "# Test Skill\n"

    def test_cli_symlink_skip_default_message_has_no_flags(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        _seed_skill(repo_home)
        project = tmp_path / "proj"
        _install_symlink(repo_home, project)

        result = cli_runner.invoke(main, ["update", "test-skill", str(project)])

        assert result.exit_code == 0, result.output
        assert "No update needed" in result.output
        assert (
            "To reinstall: skill-sync remove test-skill && "
            "skill-sync install test-skill" in result.output
        )
        assert "--agent" not in result.output
        assert "--global" not in result.output

    def test_cli_symlink_skip_agent_global_message_carries_flags(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        _seed_skill(repo_home)
        _install_symlink(repo_home, repo_home.parent, ".agents")

        result = cli_runner.invoke(
            main, ["update", "--global", "--agent", "codex", "test-skill"]
        )

        assert result.exit_code == 0, result.output
        assert "skill-sync remove test-skill --global --agent codex" in result.output
        assert "skill-sync install test-skill --global --agent codex" in result.output

    def test_cli_symlink_skip_agent_only_message_carries_agent_flag(
        self, cli_runner: CliRunner, repo_home: Path, tmp_path: Path
    ) -> None:
        _seed_skill(repo_home)
        project = tmp_path / "proj"
        _install_symlink(repo_home, project, ".agents")

        result = cli_runner.invoke(
            main, ["update", "--agent", "codex", "test-skill", str(project)]
        )

        assert result.exit_code == 0, result.output
        assert "skill-sync remove test-skill --agent codex" in result.output
        assert "skill-sync install test-skill --agent codex" in result.output
        assert "--global" not in result.output

    def test_cli_global_with_explicit_project_errors(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        project = tmp_path / "proj"
        project.mkdir()

        result = cli_runner.invoke(
            main, ["update", "--global", "test-skill", str(project)]
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output
