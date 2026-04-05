"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.config import (
    SkillSyncConfig,
    create_default_config,
    expand_path,
    get_default_repo_path,
    load_config,
)
from dl_skills_manager.core.exceptions import ConfigError


class TestExpandPath:
    """Tests for expand_path function."""

    def test_expand_path_with_tilde(self) -> None:
        """Test that ~ is expanded to user home."""
        result = expand_path("~/.skill-sync")
        assert str(result).startswith(str(Path.home()))
        assert "~" not in str(result)

    def test_expand_path_without_tilde(self) -> None:
        """Test that paths without ~ are unchanged."""
        result = expand_path("/some/absolute/path")
        assert result == Path("/some/absolute/path")


class TestGetDefaultRepoPath:
    """Tests for get_default_repo_path function."""

    def test_returns_path_with_tilde(self) -> None:
        """Test default path contains .skill-sync."""
        result = get_default_repo_path()
        assert ".skill-sync" in str(result)


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_returns_default_values(self) -> None:
        """Test default config has expected values."""
        repo_path = Path("/test/.skill-sync")
        skills_store = Path("/test/.skill-sync/skills")
        config = create_default_config(repo_path, skills_store)

        assert isinstance(config, SkillSyncConfig)
        assert config.path == repo_path
        assert config.skills_store == skills_store
        assert config.default_link_mode == "copy"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_raises_error_when_config_missing(self, tmp_path: Path) -> None:
        """Test ConfigError when config.toml doesn't exist."""
        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=tmp_path / ".skill-sync",
            ),
            pytest.raises(ConfigError, match="Config file not found"),
        ):
            load_config()

    def test_loads_valid_config(self, tmp_path: Path) -> None:
        """Test loading a valid config.toml."""
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        config_path = repo_path / "config.toml"
        skills_store = tmp_path / "skills"
        skills_store.mkdir()
        config_path.write_text(
            """[basic]
path = "~/.skill-sync"
skills_store = "/tmp/skills"

[settings]
default_link_mode = "copy"
"""
        )

        with patch(
            "dl_skills_manager.core.config.get_default_repo_path",
            return_value=repo_path,
        ):
            config = load_config()

        assert config.path == Path.home() / ".skill-sync"
        assert config.skills_store == Path("/tmp/skills")  # noqa: S108
        assert config.default_link_mode == "copy"

    def test_uses_defaults_for_missing_fields(self, tmp_path: Path) -> None:
        """Test defaults are used when fields are missing."""
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        config_path = repo_path / "config.toml"
        config_path.write_text(
            """[basic]
skills_store = "/custom/skills"
"""
        )

        with patch(
            "dl_skills_manager.core.config.get_default_repo_path",
            return_value=repo_path,
        ):
            config = load_config()

        assert config.default_link_mode == "copy"
        # path defaults to repo_path
        assert config.path == repo_path
        assert config.skills_store == Path("/custom/skills")

    def test_raises_error_for_invalid_link_mode(self, tmp_path: Path) -> None:
        """Test ConfigError when default_link_mode is invalid."""
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        config_path = repo_path / "config.toml"
        config_path.write_text(
            """[basic]
skills_store = "/tmp/skills"

[settings]
default_link_mode = "invalid"
"""
        )

        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=repo_path,
            ),
            pytest.raises(ConfigError, match="default_link_mode"),
        ):
            load_config()
