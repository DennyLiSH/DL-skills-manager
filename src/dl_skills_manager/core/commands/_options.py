"""Shared CLI option definitions for commands with an agent target.

Single owner of the PROJECT/--global/--agent adapter boilerplate that
install/update/remove/mklink share: option definitions, defaults,
help texts, and the mutual-exclusion guard.
"""

__all__ = ["reject_global_with_project", "target_options"]

from collections.abc import Callable
from typing import Any

import click

_GLOBAL_HELP = "Operate on the agent's global skills dir instead of a PROJECT."
_DEFAULT_AGENT_HELP = "Target agent dir (claude/codex/pi/zcode/workbuddy or [agents])."


def target_options(
    *, agent_help: str = _DEFAULT_AGENT_HELP
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Attach the shared PROJECT argument and --global/--agent options.

    Commands using this decorator must call reject_global_with_project()
    as the first statement of their body (before load_config).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func = click.argument("project", default=".")(func)
        func = click.option(
            "--global",
            "is_global",
            is_flag=True,
            default=False,
            help=_GLOBAL_HELP,
        )(func)
        func = click.option(
            "--agent",
            default="claude",
            show_default=True,
            help=agent_help,
        )(func)
        return func

    return decorator


def reject_global_with_project(*, is_global: bool, project: str) -> None:
    """Raise UsageError when --global is combined with a PROJECT path."""
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")
