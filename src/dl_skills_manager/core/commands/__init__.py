"""CLI commands."""

from dl_skills_manager.core.commands.bump import bump
from dl_skills_manager.core.commands.create import create
from dl_skills_manager.core.commands.init import init
from dl_skills_manager.core.commands.install import install
from dl_skills_manager.core.commands.list import list_skills
from dl_skills_manager.core.commands.remove import remove
from dl_skills_manager.core.commands.status import status
from dl_skills_manager.core.commands.update import update
from dl_skills_manager.core.commands.verify import verify
from dl_skills_manager.core.commands.versions import versions

__all__ = [
    "bump",
    "create",
    "init",
    "install",
    "list_skills",
    "remove",
    "status",
    "update",
    "verify",
    "versions",
]
