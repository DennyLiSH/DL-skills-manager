"""Unit tests for atomic_write_toml, install_skill_copy, and update_skill_copy."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from dl_skills_manager.core.commands._shared import (
    atomic_write_toml,
    install_skill_copy,
    update_skill_copy,
)
from dl_skills_manager.core.exceptions import WriteError


class TestAtomicWriteToml:
    """Tests for atomic_write_toml function."""

    def test_write_dict(self, tmp_path: Path) -> None:
        """Test writing a dict to TOML file."""
        target = tmp_path / "config.toml"
        data = {"basic": {"key": "value"}, "settings": {"mode": "copy"}}

        atomic_write_toml(target, data)

        assert target.exists()
        content = target.read_text()
        assert "key" in content
        assert "value" in content

    def test_write_dataclass(self, tmp_path: Path) -> None:
        """Test writing a dataclass to TOML file."""

        @dataclass
        class Config:
            name: str
            version: str

        target = tmp_path / "config.toml"
        data = Config(name="test", version="1.0")

        atomic_write_toml(target, data)

        assert target.exists()
        content = target.read_text()
        assert "test" in content
        assert "1.0" in content

    def test_atomic_no_partial_write_on_failure(self, tmp_path: Path) -> None:
        """Test that failed write does not leave partial file."""
        target = tmp_path / "nonexistent" / "config.toml"

        with pytest.raises(WriteError, match="Failed to write"):
            atomic_write_toml(target, {"key": "value"})

        assert not target.exists()

    def test_overwrite_existing(self, tmp_path: Path) -> None:
        """Test overwriting an existing file."""
        target = tmp_path / "config.toml"
        target.write_text("old content")

        atomic_write_toml(target, {"new": "content"})

        content = target.read_text()
        assert "new" in content
        assert "old content" not in content


class TestInstallSkillCopy:
    """Tests for install_skill_copy function."""

    def test_install_copies_skill_to_project(self, tmp_path: Path) -> None:
        """Test that install_skill_copy copies skill directory."""
        # Setup version dir
        version_dir = tmp_path / "repo" / "test-skill"
        version_dir.mkdir(parents=True)
        (version_dir / "SKILL.md").write_text("# Test Skill\n")
        (version_dir / "helper.py").write_text("print('hello')")

        # Setup project
        project_path = tmp_path / "project"
        project_path.mkdir()
        target_skills_dir = project_path / ".claude" / "skills"

        skill_dir = tmp_path / "repo"
        result = install_skill_copy(target_skills_dir, "test-skill", skill_dir, version_dir)

        expected = target_skills_dir / "test-skill"
        assert result == expected
        assert (expected / "SKILL.md").exists()
        assert (expected / "helper.py").exists()

    def test_install_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that install_skill_copy overwrites existing skill."""
        version_dir = tmp_path / "repo" / "test-skill"
        version_dir.mkdir(parents=True)
        (version_dir / "SKILL.md").write_text("# New Version\n")

        project_path = tmp_path / "project"
        target_skills_dir = project_path / ".claude" / "skills"
        existing = target_skills_dir / "test-skill"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("# Old Version\n")

        skill_dir = tmp_path / "repo"
        install_skill_copy(target_skills_dir, "test-skill", skill_dir, version_dir)

        assert (existing / "SKILL.md").read_text() == "# New Version\n"


class TestUpdateSkillCopy:
    """Tests for update_skill_copy function."""

    def test_update_creates_backup_and_updates(self, tmp_path: Path) -> None:
        """Test update creates backup, then updates."""
        version_dir = tmp_path / "repo" / "test-skill"
        version_dir.mkdir(parents=True)
        (version_dir / "SKILL.md").write_text("# New Version\n")

        project_path = tmp_path / "project"
        target_skills_dir = project_path / ".claude" / "skills"
        installed = target_skills_dir / "test-skill"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("# Old Version\n")

        skill_dir = tmp_path / "repo"
        result = update_skill_copy(target_skills_dir, "test-skill", skill_dir, version_dir)

        assert (result / "SKILL.md").read_text() == "# New Version\n"
        # Backup should be cleaned up on success
        backup = target_skills_dir / "test-skill.bk"
        assert not backup.exists()

    def test_update_with_no_existing_install(self, tmp_path: Path) -> None:
        """Test update when skill is not yet installed."""
        version_dir = tmp_path / "repo" / "test-skill"
        version_dir.mkdir(parents=True)
        (version_dir / "SKILL.md").write_text("# Version\n")

        project_path = tmp_path / "project"
        project_path.mkdir()
        target_skills_dir = project_path / ".claude" / "skills"

        skill_dir = tmp_path / "repo"
        result = update_skill_copy(target_skills_dir, "test-skill", skill_dir, version_dir)

        assert (result / "SKILL.md").read_text() == "# Version\n"
