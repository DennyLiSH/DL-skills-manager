"""Tests for update_skill_copy (backup/restore protection + error bounds)."""

import shutil
import sys
from pathlib import Path

import pytest

from dl_skills_manager.core.commands.update import update_skill_copy
from dl_skills_manager.core.exceptions import LinkError, WriteError

# The commands package re-exports the click Command "update", which
# shadows the submodule in every attribute/getattr lookup (including
# "import ... as" and monkeypatch dotted strings). sys.modules is the
# only way to reach the module object itself.
_UPDATE_MODULE = sys.modules["dl_skills_manager.core.commands.update"]


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


def _seed(tmp_path: Path) -> tuple[Path, Path]:
    version_dir = tmp_path / "repo" / "test-skill"
    version_dir.mkdir(parents=True)
    (version_dir / "SKILL.md").write_text("# New Version\n")
    target_skills_dir = tmp_path / "project" / ".claude" / "skills"
    target_skills_dir.mkdir(parents=True)
    return version_dir, target_skills_dir


class TestUpdateSkillCopyErrorBounds:
    """Every escape path must surface as an AppError, never a bare OSError."""

    def test_backup_failure_raises_write_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        version_dir, target_skills_dir = _seed(tmp_path)
        installed = target_skills_dir / "test-skill"
        installed.mkdir()
        (installed / "SKILL.md").write_text("# Old Version\n")

        def disk_full(src: object, dst: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(shutil, "copytree", disk_full)

        with pytest.raises(WriteError, match="back up"):
            update_skill_copy(target_skills_dir, "test-skill", version_dir)

    def test_restore_failure_raises_write_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        version_dir, target_skills_dir = _seed(tmp_path)
        installed = target_skills_dir / "test-skill"
        installed.mkdir()
        (installed / "SKILL.md").write_text("# Old Version\n")

        def broken_copy(*args: object, **kwargs: object) -> None:
            raise LinkError("copy failed")

        def broken_move(src: object, dst: object) -> None:
            raise OSError("restore failed")

        monkeypatch.setattr(_UPDATE_MODULE, "copy_skill_dir", broken_copy)
        monkeypatch.setattr(shutil, "move", broken_move)

        with pytest.raises(WriteError, match="restore also failed"):
            update_skill_copy(target_skills_dir, "test-skill", version_dir)

    def test_backup_cleanup_failure_raises_write_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        version_dir, target_skills_dir = _seed(tmp_path)
        installed = target_skills_dir / "test-skill"
        installed.mkdir()
        (installed / "SKILL.md").write_text("# Old Version\n")
        (target_skills_dir / "test-skill.bk").mkdir()  # stale backup to clean up

        real_rmtree = shutil.rmtree
        bk_rmtree_calls: list[object] = []

        def flaky_rmtree(path: object) -> None:
            real_rmtree(path)
            # Only count/crack on the {name}.bk path: copy_skill_dir's
            # force-mode rmtree of the installed dir (via remove_link)
            # must keep working.
            if isinstance(path, Path) and path.name == "test-skill.bk":
                bk_rmtree_calls.append(path)
                if len(bk_rmtree_calls) > 1:  # 1st = stale bk; 2nd = success cleanup
                    raise OSError("cleanup failed")

        monkeypatch.setattr(shutil, "rmtree", flaky_rmtree)

        with pytest.raises(WriteError, match="clean up backup"):
            update_skill_copy(target_skills_dir, "test-skill", version_dir)
