"""Tests for config module."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from dl_skills_manager.core.agents import AgentDirOverride
from dl_skills_manager.core.config import (
    SkillSyncConfig,
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
"""
        )

        with patch(
            "dl_skills_manager.core.config.get_default_repo_path",
            return_value=repo_path,
        ):
            config = load_config()

        assert config.path == Path.home() / ".skill-sync"
        assert config.skills_store == Path("/tmp/skills")  # noqa: S108

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

        # path defaults to repo_path
        assert config.path == repo_path
        assert config.skills_store == Path("/custom/skills")


class TestAgentDirsParsing:
    """Tests for [agents] table parsing in load_config."""

    def _write_config(self, tmp_path: Path, extra: str = "") -> None:
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        (repo_path / "config.toml").write_text(
            "[basic]\npath = '~/.skill-sync'\nskills_store = '/tmp/skills'\n" + extra
        )

    def _load(self, tmp_path: Path) -> SkillSyncConfig:
        with patch(
            "dl_skills_manager.core.config.get_default_repo_path",
            return_value=tmp_path / ".skill-sync",
        ):
            return load_config()

    def test_no_agents_table_defaults_empty(self, tmp_path: Path) -> None:
        self._write_config(tmp_path)
        config = self._load(tmp_path)
        assert config.agent_dirs == {}

    def test_parses_overrides(self, tmp_path: Path) -> None:
        self._write_config(
            tmp_path,
            "\n[agents.codex]\n"
            "global_dir = '~/.codex/skills'\n"
            "\n"
            "[agents.mytool]\n"
            "project_dir = '.mytool/skills'\n",
        )
        config = self._load(tmp_path)
        assert config.agent_dirs["codex"] == AgentDirOverride(
            global_dir="~/.codex/skills"
        )
        assert config.agent_dirs["mytool"] == AgentDirOverride(
            project_dir=".mytool/skills"
        )

    def test_non_table_entry_raises(self, tmp_path: Path) -> None:
        self._write_config(tmp_path, "\n[agents]\ncodex = 'oops'\n")
        with pytest.raises(ConfigError, match=r"agents\.codex"):
            self._load(tmp_path)

    def test_non_string_global_dir_raises(self, tmp_path: Path) -> None:
        self._write_config(tmp_path, "\n[agents.codex]\nglobal_dir = 123\n")
        with pytest.raises(ConfigError, match="global_dir must be a string"):
            self._load(tmp_path)

    def test_non_string_project_dir_raises(self, tmp_path: Path) -> None:
        self._write_config(tmp_path, "\n[agents.codex]\nproject_dir = true\n")
        with pytest.raises(ConfigError, match="project_dir must be a string"):
            self._load(tmp_path)


class TestLegacyDefaultLinkModeWarning:
    """A leftover [settings] default_link_mode key warns, does not error."""

    def test_legacy_key_warns(
        self, fake_home: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        repo = fake_home / ".skill-sync"
        repo.mkdir()
        (repo / "config.toml").write_text(
            '[basic]\nskills_store = "/tmp/skills"\n\n'
            '[settings]\ndefault_link_mode = "symlink"\n'
        )

        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=repo,
            ),
            caplog.at_level(logging.WARNING, logger="dl_skills_manager.core.config"),
        ):
            config = load_config()

        assert config.skills_store == Path("/tmp/skills")  # noqa: S108
        assert "no longer used" in caplog.text

    def test_no_settings_key_no_warning(
        self, fake_home: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        repo = fake_home / ".skill-sync"
        repo.mkdir()
        (repo / "config.toml").write_text('[basic]\nskills_store = "/tmp/skills"\n')

        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=repo,
            ),
            caplog.at_level(logging.WARNING, logger="dl_skills_manager.core.config"),
        ):
            load_config()

        assert "no longer used" not in caplog.text
