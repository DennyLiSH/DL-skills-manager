"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest
import tomli_w
from click.testing import CliRunner


@pytest.fixture
def skills_repo_dir(tmp_path: Path) -> Path:
    """Create a temporary skills repository directory with config.toml.

    Creates the new architecture:
    - tmp_path/.skill-sync/config.toml
    - tmp_path/.skill-sync/data/
    - tmp_path/.skill-sync/data/skills/
    """
    config_dir = tmp_path / ".skill-sync"
    config_dir.mkdir()
    data_dir = config_dir / "data"
    data_dir.mkdir()
    (data_dir / "skills").mkdir()

    # Create config.toml
    config_path = config_dir / "config.toml"
    with config_path.open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(config_dir), "skills_store": str(data_dir)},
            },
            f,
        )

    return config_dir


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect Path.home() to a temp dir — the documented home seam.

    Class-level patch covers every Path.home() call site (config
    discovery and global target dir resolution alike). Env vars are
    redirected too, so expanduser()-based paths also land in tmp.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def repo_home(fake_home: Path) -> Path:
    """Initialized repo under the fake home: ~/.skill-sync/config.toml.

    CliRunner invocations against this fixture exercise the real
    load_config() path with zero patches.
    """
    repo = fake_home / ".skill-sync"
    repo.mkdir()
    data = repo / "data"
    data.mkdir()
    for sub in ("skills", ".dev", ".bk"):
        (data / sub).mkdir()
    with (repo / "config.toml").open("wb") as f:
        tomli_w.dump(
            {
                "basic": {"path": str(repo), "skills_store": str(data)},
            },
            f,
        )
    return repo
