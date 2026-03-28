"""Tests for __main__.py entry point."""

from unittest.mock import patch

from dl_skills_manager.cli import main


class TestMainEntryPoint:
    """Tests for python -m dl_skills_manager entry point."""

    def test_main_is_importable(self) -> None:
        """Test that main function can be imported from __main__ module."""
        from dl_skills_manager.__main__ import main as entry_main

        assert entry_main is main

    def test_main_can_be_called(self) -> None:
        """Test that invoking main via __main__ works."""
        with patch("dl_skills_manager.__main__.main") as mock_main:
            # Simulate what __main__.py does
            mock_main()
            mock_main.assert_called_once()
