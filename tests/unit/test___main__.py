"""Tests for __main__.py entry point."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dl_skills_manager.__main__ import run

if TYPE_CHECKING:
    from pytest import MonkeyPatch


class TestMainEntryPoint:
    """Tests for python -m dl_skills_manager entry point."""

    def test_run_calls_main(self, monkeypatch: MonkeyPatch) -> None:
        """Test that run() invokes the CLI main function."""
        main_called = False

        def mock_main() -> None:
            nonlocal main_called
            main_called = True

        monkeypatch.setattr("dl_skills_manager.__main__.main", mock_main)
        run()
        assert main_called
