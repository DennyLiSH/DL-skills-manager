"""Tests for SkillsStore: layout owner and backup naming."""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dl_skills_manager.core.exceptions import (
    SkillNotFoundError,
    ValidationError,
    VersionNotFoundError,
)
from dl_skills_manager.core.store import SkillsStore


@pytest.fixture
def store(tmp_path: Path) -> SkillsStore:
    """Store with one skill in skills/ and one .dev skill."""
    s = SkillsStore(tmp_path)
    skill = s.skills_dir() / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Current\n")
    dev = s.dev_dir("dev-skill")
    dev.mkdir(parents=True)
    (dev / "SKILL.md").write_text("# Dev\n")
    return s


class TestPaths:
    """Path queries own the layout convention."""

    def test_layout_paths(self, tmp_path: Path) -> None:
        s = SkillsStore(tmp_path)
        assert s.skills_dir() == tmp_path / "skills"
        assert s.skill_dir("a") == tmp_path / "skills" / "a"
        assert s.dev_dir("a") == tmp_path / ".dev" / "a"
        assert s.backups_dir() == tmp_path / ".bk"
        assert s.backup_dir("a", "v1") == tmp_path / ".bk" / "a@v1"

    def test_skill_dir_rejects_traversal(self, tmp_path: Path) -> None:
        s = SkillsStore(tmp_path)
        with pytest.raises(ValidationError, match="Invalid skill name"):
            s.skill_dir("../etc")


class TestFindSkill:
    def test_find_skill_valid(self, store: SkillsStore) -> None:
        assert store.find_skill("test-skill") == store.skills_dir() / "test-skill"

    def test_find_skill_not_found(self, store: SkillsStore) -> None:
        with pytest.raises(SkillNotFoundError, match="not found in repository"):
            store.find_skill("nonexistent")


class TestFindVersion:
    def test_latest_returns_skill_dir(self, store: SkillsStore) -> None:
        assert store.find_version("test-skill") == store.skills_dir() / "test-skill"

    def test_specific_version_in_skill_dir(self, store: SkillsStore) -> None:
        v = store.skills_dir() / "test-skill" / "v2026.03.23"
        v.mkdir()
        assert store.find_version("test-skill", "v2026.03.23") == v

    def test_specific_version_from_bk(self, store: SkillsStore) -> None:
        bk = store.backup_dir("test-skill", "v2026.03.20")
        bk.mkdir(parents=True)
        assert store.find_version("test-skill", "v2026.03.20") == bk

    def test_specific_version_not_found(self, store: SkillsStore) -> None:
        with pytest.raises(VersionNotFoundError, match="not found for skill"):
            store.find_version("test-skill", "v2099.99.99")

    def test_version_traversal_rejected(self, store: SkillsStore) -> None:
        """Path-bearing versions must never reach path concatenation."""
        with pytest.raises(ValidationError, match="Invalid version"):
            store.find_version("test-skill", "../evil")
        with pytest.raises(ValidationError, match="Invalid version"):
            store.find_version("test-skill", "a/b")

    def test_version_invalid_forms_rejected(self, store: SkillsStore) -> None:
        """Empty / '.' / drive-relative versions are rejected by the
        whitelist (they would escape the store or resolve to the wrong
        directory instead of erroring)."""
        for bad in ("", ".", "C:evil", "v2026.03.23/../x", "latest\x00"):
            with pytest.raises(ValidationError, match="Invalid version"):
                store.find_version("test-skill", bad)

    def test_missing_skill_raises_skill_not_found(self, store: SkillsStore) -> None:
        with pytest.raises(SkillNotFoundError):
            store.find_version("nonexistent")


class TestListBackups:
    def test_lists_versions_newest_first(self, store: SkillsStore) -> None:
        for v in ["v2026.03.20", "v2026.03.23", "v2026.03.25-dev"]:
            store.backup_dir("test-skill", v).mkdir(parents=True)
        assert store.list_backups("test-skill") == [
            "v2026.03.25-dev",
            "v2026.03.23",
            "v2026.03.20",
        ]

    def test_no_backups_or_missing_bk(self, store: SkillsStore) -> None:
        assert store.list_backups("test-skill") == []
        assert store.list_backups("nonexistent") == []


class TestListSkills:
    def test_only_dirs_with_skill_marker(self, tmp_path: Path) -> None:
        s = SkillsStore(tmp_path)
        good = s.skills_dir() / "good"
        good.mkdir(parents=True)
        (good / "SKILL.md").write_text("# x\n")
        (s.skills_dir() / "no-marker").mkdir()
        (s.skills_dir() / "file.txt").write_text("x")
        assert [si.name for si in s.list_skills()] == ["good"]

    def test_history_from_bk(self, tmp_path: Path) -> None:
        s = SkillsStore(tmp_path)
        good = s.skills_dir() / "good"
        good.mkdir(parents=True)
        (good / "SKILL.md").write_text("# x\n")
        store_backup = s.backup_dir("good", "v2026.03.22")
        store_backup.mkdir(parents=True)
        skills = s.list_skills()
        assert skills[0].name == "good"
        assert skills[0].history == ("v2026.03.22",)

    def test_empty_when_no_skills_dir(self, tmp_path: Path) -> None:
        assert SkillsStore(tmp_path).list_skills() == []


class TestNextBackupVersion:
    def _pin_mtime(self, path: Path, dt: datetime) -> None:
        ts = dt.timestamp()
        os.utime(path, (ts, ts))

    def test_base_version_from_dev_mtime(self, store: SkillsStore) -> None:
        dev_file = store.dev_dir("dev-skill") / "SKILL.md"
        self._pin_mtime(dev_file, datetime(2026, 3, 23, 12, 0, tzinfo=UTC))
        assert store.next_backup_version("dev-skill") == "v2026.03.23"

    def test_same_day_increments(self, store: SkillsStore) -> None:
        dev_file = store.dev_dir("dev-skill") / "SKILL.md"
        self._pin_mtime(dev_file, datetime(2026, 3, 23, 12, 0, tzinfo=UTC))
        store.backup_dir("dev-skill", "v2026.03.23").mkdir(parents=True)
        assert store.next_backup_version("dev-skill") == "v2026.03.23.1"
        store.backup_dir("dev-skill", "v2026.03.23.1").mkdir()
        assert store.next_backup_version("dev-skill") == "v2026.03.23.2"

    def test_dev_suffix_version_ignored_for_collision(
        self, store: SkillsStore
    ) -> None:
        dev_file = store.dev_dir("dev-skill") / "SKILL.md"
        self._pin_mtime(dev_file, datetime(2026, 3, 23, 12, 0, tzinfo=UTC))
        store.backup_dir("dev-skill", "v2026.03.23-dev").mkdir(parents=True)
        assert store.next_backup_version("dev-skill") == "v2026.03.23"


class TestPromote:
    def test_promote_copies_to_production_and_backup(
        self, store: SkillsStore
    ) -> None:
        result = store.promote("dev-skill")
        target = store.skills_dir() / "dev-skill"
        assert result.target == target
        assert (target / "SKILL.md").read_text() == "# Dev\n"
        assert result.backup == store.backup_dir("dev-skill", result.version)
        assert (result.backup / "SKILL.md").exists()
        assert result.version.startswith("v")

    def test_promote_overwrites_existing_production(
        self, store: SkillsStore
    ) -> None:
        target = store.skills_dir() / "dev-skill"
        target.mkdir(parents=True)
        (target / "SKILL.md").write_text("# Old\n")
        store.promote("dev-skill")
        assert (target / "SKILL.md").read_text() == "# Dev\n"

    def test_promote_dev_not_found(self, store: SkillsStore) -> None:
        with pytest.raises(SkillNotFoundError, match=r"not found in \.dev/"):
            store.promote("nonexistent")

    def test_promote_dev_without_skill_marker(
        self, tmp_path: Path
    ) -> None:
        s = SkillsStore(tmp_path)
        dev = s.dev_dir("markerless")
        dev.mkdir(parents=True)
        (dev / "README.md").write_text("x")
        with pytest.raises(SkillNotFoundError, match=r"no SKILL\.md"):
            s.promote("markerless")
