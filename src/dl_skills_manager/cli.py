"""DL Skills Manager CLI - Claude Code Skills Repository Manager.

A CLI tool for managing Claude Code skills with centralized storage
and on-demand linking to projects.
"""

from __future__ import annotations

import logging
import sys

import click

from dl_skills_manager.core.commands.bump import bump
from dl_skills_manager.core.commands.create import create
from dl_skills_manager.core.commands.init import init
from dl_skills_manager.core.commands.install import install
from dl_skills_manager.core.commands.list import list_cmd as list_skills
from dl_skills_manager.core.commands.remove import remove
from dl_skills_manager.core.commands.status import status
from dl_skills_manager.core.commands.update import update
from dl_skills_manager.core.commands.verify import verify
from dl_skills_manager.core.commands.versions import versions
from dl_skills_manager.core.exceptions import AppError


class ErrorHandlingCommand(click.Command):
    """A Click Command that wraps AppError exceptions for proper error display."""

    def invoke(self, ctx: click.Context) -> None:
        """Invoke the command with error handling for AppError exceptions."""
        try:
            super().invoke(ctx)
        except AppError as e:
            error_type = type(e).__name__
            click.secho(f"[{error_type}] {e}", fg="red", err=True)
            raise SystemExit(1) from e


def _make_error_handling_cmd(cmd: click.Command) -> ErrorHandlingCommand:
    """Wrap a click Command to handle AppError exceptions.

    Args:
        cmd: The command to wrap.

    Returns:
        An ErrorHandlingCommand instance with the same settings.
    """
    wrapped = ErrorHandlingCommand(
        name=cmd.name or "unknown",
        context_settings=cmd.context_settings,
        callback=cmd.callback,
        help=cmd.help,
        epilog=cmd.epilog,
        short_help=cmd.short_help,
        options_metavar=cmd.options_metavar,
        add_help_option=cmd.add_help_option,
        no_args_is_help=cmd.no_args_is_help,
        hidden=cmd.hidden,
        deprecated=cmd.deprecated,
    )
    # Copy over the params from original command
    for param in cmd.params:
        if param.name not in ("help",):
            wrapped.params.append(param)
    return wrapped


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
main.add_command(_make_error_handling_cmd(init))
main.add_command(_make_error_handling_cmd(list_skills), name="list")
main.add_command(_make_error_handling_cmd(create))
main.add_command(_make_error_handling_cmd(install))
main.add_command(_make_error_handling_cmd(remove))
main.add_command(_make_error_handling_cmd(update))
main.add_command(_make_error_handling_cmd(bump))
main.add_command(_make_error_handling_cmd(verify))
main.add_command(_make_error_handling_cmd(versions))
main.add_command(_make_error_handling_cmd(status))


if __name__ == "__main__":
    main()
