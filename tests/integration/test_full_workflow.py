"""Full workflow integration tests (fake_home/repo_home, zero patches)."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import tomli_w

from dl_skills_manager.cli import main

if TYPE_CHECKING:
    from click.testing import CliRunner


class TestWorkflow:
    """Test complete workflows."""

    def test_init_creates_structure(
        self, cli_runner: CliRunner, fake_home: Path
    ) -> None:
        result = cli_runner.invoke(
            main,
            ["init", "--skills-path", str(fake_home / "skills")],
            # Pre-Plan-4 init still prompts for link mode and consumes
            # this input; after Plan 4 removes the prompt the leftover
            # stdin is simply ignored — green in both windows.
            input="copy\n",
        )

        assert result.exit_code == 0, result.output
        assert (fake_home / ".skill-sync" / "config.toml").exists()

    def test_create_and_list_workflow(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        pytest.skip("create command is TBD")

    def test_multi_agent_install_update(
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        """End-to-end: real config load → install --agent codex → update."""
        skill = repo_home / "data" / "skills" / "demo-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# demo\n")
        fake_home = repo_home.parent

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
        self, cli_runner: CliRunner, repo_home: Path
    ) -> None:
        """[agents] override flows through real config load → install."""
        skill = repo_home / "data" / "skills" / "demo-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# demo\n")
        fake_home = repo_home.parent

        with (repo_home / "config.toml").open("wb") as f:
            tomli_w.dump(
                {
                    "basic": {
                        "path": str(repo_home),
                        "skills_store": str(repo_home / "data"),
                    },
                    "agents": {"codex": {"global_dir": "~/.codex/skills"}},
                },
                f,
            )

        result = cli_runner.invoke(
            main,
            ["install", "--global", "--agent", "codex", "demo-skill"],
        )

        assert result.exit_code == 0, result.output
        assert (fake_home / ".codex" / "skills" / "demo-skill").exists()
