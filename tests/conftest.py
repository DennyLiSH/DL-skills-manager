"""Pytest configuration and fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def skills_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary skills repository directory."""
    repo_dir = tmp_path / ".skills-repo"
    repo_dir.mkdir()
    return repo_dir


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()
