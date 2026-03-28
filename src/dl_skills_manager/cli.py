"""DL Skills Manager CLI - Claude Code Skills Repository Manager.

A CLI tool for managing Claude Code skills with centralized storage
and on-demand linking to projects.
"""

__all__ = ["main"]

import logging
import sys
from functools import wraps
from typing import Any

import click

from dl_skills_manager.core.commands.init import init
from dl_skills_manager.core.commands.install import install
from dl_skills_manager.core.commands.list import list_skills_cmd
from dl_skills_manager.core.commands.mtp import mtp
from dl_skills_manager.core.commands.remove import remove
from dl_skills_manager.core.commands.update import update
from dl_skills_manager.core.commands.versions import versions
from dl_skills_manager.core.exceptions import AppError


def _handle_app_errors(cmd: click.Command) -> click.Command:
    """Decorator to wrap a click Command with AppError exception handling.

    Args:
        cmd: The command to wrap.

    Returns:
        The wrapped command.
    """
    original_callback = cmd.callback

    @wraps(cmd)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            if original_callback is not None:
                return original_callback(*args, **kwargs)
            raise RuntimeError("Command has no callback")
        except AppError as e:
            error_type = type(e).__name__
            click.secho(f"Error: [{error_type}] {e}", fg="red", err=True)
            raise SystemExit(1) from None

    cmd.callback = wrapper
    return cmd


@click.group()
def main() -> None:
    """DL Skills Manager - Claude Code Skills Repository Manager.

    A CLI tool for managing Claude Code skills with centralized storage
    and on-demand linking to projects.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )


# Register commands with error handling
main.add_command(_handle_app_errors(init))
main.add_command(_handle_app_errors(list_skills_cmd), name="list")
main.add_command(_handle_app_errors(install))
main.add_command(_handle_app_errors(mtp))
main.add_command(_handle_app_errors(remove))
main.add_command(_handle_app_errors(update))
main.add_command(_handle_app_errors(versions))


if __name__ == "__main__":
    main()
