"""Unit tests for update_skill_copy."""

from pathlib import Path

from dl_skills_manager.core.commands._shared import update_skill_copy


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

        result = update_skill_copy(target_skills_dir, "test-skill", version_dir)

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

        result = update_skill_copy(target_skills_dir, "test-skill", version_dir)

        assert (result / "SKILL.md").read_text() == "# Version\n"
