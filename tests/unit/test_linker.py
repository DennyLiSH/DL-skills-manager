"""Tests for linker module."""

import errno
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.exceptions import LinkError
from dl_skills_manager.core.linker import (
    _is_permission_error,
    create_link,
    is_link_valid,
    remove_link,
)


class TestCreateLink:
    """Tests for create_link function."""

    def test_raises_error_when_source_missing(self, tmp_path: Path) -> None:
        """Test LinkError when source doesn't exist."""
        source = tmp_path / "nonexistent"
        target = tmp_path / "link"

        with pytest.raises(LinkError, match="Source does not exist"):
            create_link(source, target)

    def test_returns_false_when_target_exists(self, tmp_path: Path) -> None:
        """Test raises LinkError when target already exists."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"
        target.write_text("existing")

        with pytest.raises(LinkError, match="already exists"):
            create_link(source, target)

    def test_creates_symlink(self, tmp_path: Path) -> None:
        """Test symlink creation."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("content")
        target = tmp_path / "link"

        create_link(source, target)

        assert target.is_symlink() or target.is_dir()

    def test_force_removes_existing(self, tmp_path: Path) -> None:
        """Test force=True removes existing target."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"
        target.write_text("old")

        create_link(source, target, force=True)

        assert target.is_symlink() or target.is_dir()


class TestRemoveLink:
    """Tests for remove_link function."""

    def test_returns_false_when_target_missing(self, tmp_path: Path) -> None:
        """Test raises LinkError when target doesn't exist."""
        with pytest.raises(LinkError, match="does not exist"):
            remove_link(tmp_path / "nonexistent")

    def test_removes_symlink(self, tmp_path: Path) -> None:
        """Test symlink removal."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"
        target.symlink_to(source)

        remove_link(target)

        assert not target.exists()

    def test_removes_copied_directory(self, tmp_path: Path) -> None:
        """Test copied directory removal."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("content")
        target = tmp_path / "target"

        # Copy instead of symlink (simulate by creating real dir)
        shutil.copytree(source, target)

        remove_link(target)

        assert not target.exists()


class TestIsLinkValid:
    """Tests for is_link_valid function."""

    def test_returns_false_for_nonexistent_path(self, tmp_path: Path) -> None:
        """Test False when path doesn't exist."""
        assert is_link_valid(tmp_path / "nonexistent") is False

    def test_returns_false_for_regular_file(self, tmp_path: Path) -> None:
        """Test False for regular file (not symlink)."""
        file = tmp_path / "file.txt"
        file.write_text("content")
        assert is_link_valid(file) is False

    def test_returns_true_for_valid_symlink(self, tmp_path: Path) -> None:
        """Test True for valid symlink."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"
        target.symlink_to(source)

        assert is_link_valid(target) is True

    def test_returns_false_for_broken_symlink(self, tmp_path: Path) -> None:
        """Test False for broken symlink."""
        target = tmp_path / "broken_link"
        target.symlink_to(tmp_path / "nonexistent")

        assert is_link_valid(target) is False


class TestIsPermissionError:
    """Tests for _is_permission_error function."""

    def test_returns_true_for_eacces(self) -> None:
        """Test EACCES is detected as permission error."""
        error = OSError(errno.EACCES, "Permission denied")
        assert _is_permission_error(error) is True

    def test_returns_true_for_eperm(self) -> None:
        """Test EPERM is detected as permission error."""
        error = OSError(getattr(errno, "EPERM", 13), "Operation not permitted")
        assert _is_permission_error(error) is True

    def test_returns_false_for_other_errors(self) -> None:
        """Test non-permission errors return False."""
        error = OSError(errno.ENOENT, "No such file")
        assert _is_permission_error(error) is False


class TestCreateLinkFallback:
    """Tests for create_link fallback to copy on permission error."""

    def test_fallback_to_copy_when_symlink_fails(self, tmp_path: Path) -> None:
        """Test symlink failure falls back to copy."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("content")
        target = tmp_path / "link"

        perm_error = OSError(errno.EACCES, "Permission denied")
        with patch.object(Path, "symlink_to", side_effect=perm_error):
            create_link(source, target)

        assert target.is_dir()
        assert (target / "file.txt").read_text() == "content"

    def test_raises_link_error_when_copy_also_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Test LinkError when both symlink and copy fail."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"

        perm_error = OSError(errno.EACCES, "Permission denied")
        space_error = OSError(errno.ENOSPC, "No space left")
        with (
            patch.object(Path, "symlink_to", side_effect=perm_error),
            patch.object(shutil, "copytree", side_effect=space_error),
            pytest.raises(LinkError, match="Failed to create link"),
        ):
            create_link(source, target)

    def test_raises_link_error_for_non_permission_oserror(
        self,
        tmp_path: Path,
    ) -> None:
        """Test LinkError for non-permission OSError."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "link"

        notfound_error = OSError(errno.ENOENT, "No such file")
        with (
            patch.object(Path, "symlink_to", side_effect=notfound_error),
            pytest.raises(LinkError, match="Failed to create symlink"),
        ):
            create_link(source, target)
