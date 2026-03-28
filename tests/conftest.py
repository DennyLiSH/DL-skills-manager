"""Pytest configuration and fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import tomli_w
from click.testing import CliRunner


@pytest.fixture
def skills_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary skills repository directory with config.toml.

    Creates the new architecture:
    - tmp_path/.skill-sync/config.toml
    - tmp_path/.skill-sync/skills/
    """
    config_dir = tmp_path / ".skill-sync"
    config_dir.mkdir()
    skills_dir = config_dir / "skills"
    skills_dir.mkdir()

    # Create config.toml
    config_path = config_dir / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(config_dir), "skills_store": str(skills_dir)},
                "settings": {"default_link_mode": "symlink", "fallback_to_copy": True},
            },
            f,
        )

    return config_dir


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()
