"""Tests for init command (core function + CLI adapter)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from dl_skills_manager.cli import main
from dl_skills_manager.core.commands.init import InitResult, init_repo
from dl_skills_manager.core.exceptions import RepoAlreadyExistsError

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestInitRepoCore:
    """Core function tests: explicit repo_path, no patches."""

    def test_creates_default_layout(self, tmp_path: Path) -> None:
        repo = tmp_path / ".skill-sync"

        result = init_repo(skills_path=None, link_mode="copy", repo_path=repo)

        assert isinstance(result, InitResult)
        assert (repo / "config.toml").exists()
        for sub in ("skills", ".dev", ".bk", "agents"):
            assert (repo / "data" / sub).is_dir()
        assert (repo / "data" / ".claude-plugin" / "marketplace.json").exists()
        assert result.repo_path == repo
        assert result.skills_store == repo / "data"

    def test_custom_skills_path(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom-store"

        result = init_repo(
            skills_path=str(custom),
            link_mode="copy",
            repo_path=tmp_path / ".skill-sync",
        )

        assert (custom / "skills").is_dir()
        assert (custom / ".claude-plugin" / "marketplace.json").exists()
        assert result.skills_store == custom

    def test_already_initialized_raises(self, tmp_path: Path) -> None:
        repo = tmp_path / ".skill-sync"
        init_repo(skills_path=None, link_mode="copy", repo_path=repo)

        with pytest.raises(RepoAlreadyExistsError, match="already initialized"):
            init_repo(skills_path=None, link_mode="copy", repo_path=repo)


class TestInitCommand:
    """CLI adapter tests via fake_home (real get_default_repo_path, zero patches)."""

    def test_init_creates_repo_structure(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        repo = fake_home / ".skill-sync"

        result = cli_runner.invoke(
            main,
            ["init", "--skills-path", str(fake_home / "skills"), "--link-mode", "copy"],
        )

        assert result.exit_code == 0, result.output
        assert (repo / "config.toml").exists()

    def test_init_creates_config_file(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            [
                "init",
                "--skills-path",
                str(fake_home / "custom-skills"),
                "--link-mode",
                "copy",
            ],
        )

        assert result.exit_code == 0, result.output
        content = (fake_home / ".skill-sync" / "config.toml").read_text()
        assert "[basic]" in content
        assert "skills_store" in content

    def test_init_already_exists(self, cli_runner: CliRunner, fake_home: Path) -> None:
        repo = fake_home / ".skill-sync"
        repo.mkdir(parents=True)
        (repo / "config.toml").write_text("[basic]\n")

        result = cli_runner.invoke(main, ["init"])

        assert result.exit_code == 1
        assert "already initialized" in result.output

    def test_init_default_skills_path(self, cli_runner: CliRunner) -> None:
        result = cli_runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--skills-path" in result.output


class TestInitLinkMode:
    """init link-mode prompt behavior (via fake_home)."""

    def test_init_prompts_when_link_mode_not_specified(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            ["init", "--skills-path", str(fake_home / "skills")],
            input="copy\n",
        )

        assert result.exit_code == 0, result.output
        assert "Default installation mode" in result.output

    def test_init_accepts_default_copy_via_prompt(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            ["init", "--skills-path", str(fake_home / "skills")],
            input="\n",
        )

        assert result.exit_code == 0, result.output
        assert "copy" in (fake_home / ".skill-sync" / "config.toml").read_text()

    def test_init_link_mode_option_skips_prompt(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            [
                "init",
                "--skills-path",
                str(fake_home / "skills"),
                "--link-mode",
                "symlink",
            ],
        )

        assert result.exit_code == 0, result.output
        assert "Default installation mode" not in result.output
        assert "symlink" in (fake_home / ".skill-sync" / "config.toml").read_text()
