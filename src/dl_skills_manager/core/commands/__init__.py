"""CLI commands."""

from dl_skills_manager.core.commands.init import init
from dl_skills_manager.core.commands.install import install
from dl_skills_manager.core.commands.list import list_skills
from dl_skills_manager.core.commands.mtp import mtp
from dl_skills_manager.core.commands.remove import remove
from dl_skills_manager.core.commands.update import update
from dl_skills_manager.core.commands.versions import versions

__all__ = [
    "init",
    "install",
    "list_skills",
    "mtp",
    "remove",
    "update",
    "versions",
]
