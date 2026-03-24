"""Tests for config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dl_skills_manager.core.config import (
    RepoConfig,
    create_default_config,
    expand_path,
    get_default_repo_path,
    load_repo_config,
)
from dl_skills_manager.core.exceptions import ConfigError


class TestExpandPath:
    """Tests for expand_path function."""

    def test_expand_path_with_tilde(self) -> None:
        """Test that ~ is expanded to user home."""
        result = expand_path("~/.skills-repo")
        assert str(result).startswith(str(Path.home()))
        assert "~" not in str(result)

    def test_expand_path_without_tilde(self) -> None:
        """Test that paths without ~ are unchanged."""
        result = expand_path("/some/absolute/path")
        assert result == Path("/some/absolute/path")


class TestGetDefaultRepoPath:
    """Tests for get_default_repo_path function."""

    def test_returns_path_with_tilde(self) -> None:
        """Test default path contains .skills-repo."""
        result = get_default_repo_path()
        assert ".skills-repo" in str(result)


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_returns_default_values(self) -> None:
        """Test default config has expected values."""
        repo_path = Path("/test/repo")
        config = create_default_config(repo_path)

        assert isinstance(config, RepoConfig)
        assert config.name == "my-skills"
        assert config.path == repo_path
        assert config.default_link_mode == "symlink"
        assert config.fallback_to_copy is True


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""

    def test_raises_error_when_config_missing(self, tmp_path: Path) -> None:
        """Test ConfigError when config.toml doesn't exist."""
        with pytest.raises(ConfigError, match="Config file not found"):
            load_repo_config(tmp_path)

    def test_loads_valid_config(self, tmp_path: Path) -> None:
        """Test loading a valid config.toml."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """[repo]
name = "test-repo"
path = "~/.test-repo"

[settings]
default_link_mode = "copy"
fallback_to_copy = false
"""
        )

        config = load_repo_config(tmp_path)

        assert config.name == "test-repo"
        assert config.default_link_mode == "copy"
        assert config.fallback_to_copy is False

    def test_uses_defaults_for_missing_fields(self, tmp_path: Path) -> None:
        """Test defaults are used when fields are missing."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """[repo]
name = "minimal-repo"
"""
        )

        config = load_repo_config(tmp_path)

        assert config.name == "minimal-repo"
        assert config.default_link_mode == "symlink"
        assert config.fallback_to_copy is True
