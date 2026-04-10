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
