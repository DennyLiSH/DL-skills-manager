"""CLI entry point - supports: python -m dl_skills_manager"""

from dl_skills_manager.cli import main


def run() -> None:
    """Entry point for python -m dl_skills_manager."""
    main()


if __name__ == "__main__":
    run()
