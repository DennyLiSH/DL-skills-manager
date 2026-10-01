"""Full workflow integration tests."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestWorkflow:
    """Test complete workflows."""

    def test_init_creates_structure(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test that init creates correct directory structure."""
        mock_config_path = tmp_path / ".skill-sync"

        with patch(
            "dl_skills_manager.core.commands.init.get_default_repo_path",
            return_value=mock_config_path,
        ):
            result = cli_runner.invoke(
                main,
                [
                    "init",
                    "--skills-path",
                    str(tmp_path / "skills"),
                    "--link-mode",
                    "copy",
                ],
            )

        assert result.exit_code == 0
        assert (mock_config_path / "config.toml").exists()

    def test_create_and_list_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test create and list workflow - skipped since create is TBD."""
        pytest.skip("create command is TBD")

    def test_multi_agent_install_update(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """End-to-end: real config load → install --agent codex → update."""
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        store = tmp_path / "store"
        skills_dir = store / "skills" / "demo-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# demo\n")

        with (repo_path / "config.toml").open("wb") as f:
            tomli_w.dump(
                {
                    "basic": {"path": str(repo_path), "skills_store": str(store)},
                    "settings": {"default_link_mode": "copy"},
                },
                f,
            )

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=repo_path,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.Path.home",
                return_value=fake_home,
            ),
        ):
            install_result = cli_runner.invoke(
                main,
                [
                    "install",
                    "--global",
                    "--agent",
                    "codex",
                    "--link-mode",
                    "symlink",
                    "demo-skill",
                ],
            )
            update_result = cli_runner.invoke(
                main,
                ["update", "--global", "--agent", "codex", "demo-skill"],
            )

        assert install_result.exit_code == 0, install_result.output
        assert (fake_home / ".agents" / "skills" / "demo-skill").exists()

        assert update_result.exit_code == 0, update_result.output
        output = update_result.output.lower()
        # symlink privilege present → skip message; absent → copy fallback update
        assert "symlink" in output or "updated" in output

    def test_multi_agent_config_override_install(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """[agents] override flows through real config load → install."""
        repo_path = tmp_path / ".skill-sync"
        repo_path.mkdir()
        store = tmp_path / "store"
        skills_dir = store / "skills" / "demo-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# demo\n")

        with (repo_path / "config.toml").open("wb") as f:
            tomli_w.dump(
                {
                    "basic": {"path": str(repo_path), "skills_store": str(store)},
                    "settings": {"default_link_mode": "copy"},
                    "agents": {"codex": {"global_dir": "~/.codex/skills"}},
                },
                f,
            )

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with (
            patch(
                "dl_skills_manager.core.config.get_default_repo_path",
                return_value=repo_path,
            ),
            patch(
                "dl_skills_manager.core.commands._shared.Path.home",
                return_value=fake_home,
            ),
        ):
            result = cli_runner.invoke(
                main,
                ["install", "--global", "--agent", "codex", "demo-skill"],
            )

        assert result.exit_code == 0, result.output
        assert (fake_home / ".codex" / "skills" / "demo-skill").exists()
