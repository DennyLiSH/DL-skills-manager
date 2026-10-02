"""Tests for mklink command."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    """Create a source directory with two valid skills and one invalid."""
    source = tmp_path / "skills-source"
    source.mkdir()

    # Valid skill a
    skill_a = source / "skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("# Skill A\n")

    # Valid skill b
    skill_b = source / "skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text("# Skill B\n")

    # Invalid: directory without SKILL.md
    no_skill = source / "not-a-skill"
    no_skill.mkdir()
    (no_skill / "README.md").write_text("No skill marker\n")

    # Invalid: hidden directory
    hidden = source / ".hidden-skill"
    hidden.mkdir()
    (hidden / "SKILL.md").write_text("# Hidden\n")

    # Invalid: plain file (not a directory)
    (source / "some-file.txt").write_text("not a dir\n")

    return source


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a project directory."""
    project = tmp_path / "my-project"
    project.mkdir()
    return project


class TestMklinkCommand:
    """Tests for mklink command."""

    def test_mklink_basic(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test linking 2 valid skills to project."""
        result = cli_runner.invoke(
            main,
            ["mklink", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        assert "Linked skill-a" in result.output
        assert "Linked skill-b" in result.output
        assert "Linked 2 skill(s)" in result.output

        # Verify both skills exist in target
        target = project_dir / ".claude" / "skills"
        assert (target / "skill-a").exists()
        assert (target / "skill-b").exists()

    def test_mklink_skips_non_skill_dirs(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test that dirs without SKILL.md are skipped."""
        result = cli_runner.invoke(
            main,
            ["mklink", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        target = project_dir / ".claude" / "skills"
        assert not (target / "not-a-skill").exists()

    def test_mklink_skips_hidden_dirs(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test that hidden dirs (starting with .) are skipped."""
        result = cli_runner.invoke(
            main,
            ["mklink", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        target = project_dir / ".claude" / "skills"
        assert not (target / ".hidden-skill").exists()

    def test_mklink_with_prefix(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test --prefix is prepended to symlink names."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--prefix", "gstack-", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        assert "Linked gstack-skill-a" in result.output
        assert "Linked gstack-skill-b" in result.output

        target = project_dir / ".claude" / "skills"
        assert (target / "gstack-skill-a").exists()
        assert (target / "gstack-skill-b").exists()

    def test_mklink_empty_source(
        self, cli_runner: CliRunner, tmp_path: Path, project_dir: Path
    ) -> None:
        """Test source dir with no valid skills."""
        empty_source = tmp_path / "empty"
        empty_source.mkdir()

        result = cli_runner.invoke(
            main,
            ["mklink", str(empty_source), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        assert "Linked 0 skill(s)" in result.output

    def test_mklink_path_traversal(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test that path traversal via --prefix is rejected."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--prefix", "../", str(source_dir), str(project_dir)],
        )

        # Should fail because validate_skill_name rejects "../skill-a"
        assert result.exit_code != 0
        assert "Invalid" in result.output

    def test_mklink_overwrites_existing(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test that existing skills are overwritten (force=True)."""
        # Create a pre-existing skill in target
        target = project_dir / ".claude" / "skills"
        target.mkdir(parents=True)
        existing = target / "skill-a"
        existing.mkdir()
        (existing / "SKILL.md").write_text("# Old Version\n")

        result = cli_runner.invoke(
            main,
            ["mklink", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        # Skill-a should be overwritten
        assert (target / "skill-a").exists()

    def test_mklink_nonexistent_source(
        self, cli_runner: CliRunner, project_dir: Path
    ) -> None:
        """Test error when source path doesn't exist."""
        result = cli_runner.invoke(
            main,
            ["mklink", "/nonexistent/path", str(project_dir)],
        )

        assert result.exit_code != 0

    def test_mklink_mixed_files_and_dirs(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test that plain files in source dir are ignored."""
        result = cli_runner.invoke(
            main,
            ["mklink", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        # some-file.txt should not be mentioned
        assert "some-file" not in result.output

    def test_mklink_global(
        self, cli_runner: CliRunner, source_dir: Path, fake_home: Path
    ) -> None:
        """Test --global links to ~/.claude/skills/ (fake home)."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--global", str(source_dir)],
        )

        assert result.exit_code == 0, result.output
        assert "Linked skill-a" in result.output
        assert (fake_home / ".claude" / "skills" / "skill-a").exists()
        assert (fake_home / ".claude" / "skills" / "skill-b").exists()

    def test_mklink_global_and_project_conflict(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """Test --global with explicit project path raises error."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--global", str(source_dir), str(project_dir)],
        )

        assert result.exit_code != 0
        assert "Cannot specify both --global and a PROJECT path" in result.output

    def test_mklink_agent_codex_project(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        """--agent codex links into <project>/.agents/skills/."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--agent", "codex", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        assert (project_dir / ".agents" / "skills" / "skill-a").exists()
        assert (project_dir / ".agents" / "skills" / "skill-b").exists()

    def test_mklink_agent_pi_global(
        self, cli_runner: CliRunner, source_dir: Path, fake_home: Path
    ) -> None:
        """--agent pi --global links into ~/.pi/agent/skills/."""
        result = cli_runner.invoke(
            main,
            ["mklink", "--agent", "pi", "--global", str(source_dir)],
        )

        assert result.exit_code == 0, result.output
        assert (fake_home / ".pi" / "agent" / "skills" / "skill-a").exists()

    def test_mklink_unknown_agent_errors(
        self, cli_runner: CliRunner, source_dir: Path, project_dir: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            ["mklink", "--agent", "nope", str(source_dir), str(project_dir)],
        )

        assert result.exit_code != 0
        assert "Unknown agent" in result.output

    def test_mklink_ignores_agents_config(
        self, cli_runner: CliRunner, source_dir: Path, repo_home: Path
    ) -> None:
        """D6 guard: mklink never reads [agents] config overrides.

        A real config.toml with a codex override exists, yet mklink must
        still resolve codex to the builtin ~/.agents/skills/.
        """
        with (repo_home / "config.toml").open("ab") as f:
            f.write(b"\n[agents.codex]\nglobal_dir = '~/.codex/skills'\n")

        result = cli_runner.invoke(
            main,
            ["mklink", "--agent", "codex", "--global", str(source_dir)],
        )

        assert result.exit_code == 0, result.output
        home = repo_home.parent
        assert (home / ".agents" / "skills" / "skill-a").exists()
        assert not (home / ".codex" / "skills").exists()

    def test_mklink_ignores_agents_config_project(
        self,
        cli_runner: CliRunner,
        source_dir: Path,
        project_dir: Path,
        repo_home: Path,
    ) -> None:
        """D6 guard, project branch: [agents] project_dir overrides are ignored.

        A real config.toml with a codex project_dir override exists and
        sits at the real discovery path — if mklink ever wires
        agent_overrides into the project branch, links would land in
        .codex-override/ and the reverse assertion below would trip.
        """
        with (repo_home / "config.toml").open("ab") as f:
            f.write(b"\n[agents.codex]\nproject_dir = '.codex-override/skills'\n")

        result = cli_runner.invoke(
            main,
            ["mklink", "--agent", "codex", str(source_dir), str(project_dir)],
        )

        assert result.exit_code == 0, result.output
        assert (project_dir / ".agents" / "skills" / "skill-a").exists()
        assert not (project_dir / ".codex-override").exists()
