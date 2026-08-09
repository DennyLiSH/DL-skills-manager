"""mklink command - batch symlink skills from an arbitrary source directory."""

from pathlib import Path

import click

from dl_skills_manager.core.commands._shared import (
    resolve_skills_target_dir,
    validate_skill_name,
)
from dl_skills_manager.core.linker import create_link

SKILL_MARKER = "SKILL.md"


@click.command()
@click.argument("source_path", type=click.Path(exists=True, file_okay=False))
@click.argument("project", default=".", required=False)
@click.option("--prefix", default="", help="Symlink name prefix (e.g. 'gstack-')")
@click.option(
    "--global",
    "is_global",
    is_flag=True,
    default=False,
    help="Link to ~/.claude/skills/ instead of a project.",
)
def mklink(source_path: str, project: str, prefix: str, is_global: bool) -> None:
    """Batch symlink skills from SOURCE_PATH to project's .claude/skills/.

    Scans SOURCE_PATH for subdirectories containing SKILL.md and creates
    symlinks (or copies on Windows without symlink privilege) in the
    project's .claude/skills/ directory.

    Use --prefix to namespace linked skills (e.g. --prefix gstack-).
    Use --global to link to ~/.claude/skills/ instead.
    """
    if is_global and project != ".":
        raise click.UsageError("Cannot specify both --global and a PROJECT path.")

    source_dir = Path(source_path).resolve()

    if is_global:
        target_dir = resolve_skills_target_dir(global_flag=True)
    else:
        project_dir = Path(project).resolve()
        target_dir = resolve_skills_target_dir(
            global_flag=False,
            project_path=project_dir,
        )

    linked = 0
    for subdir in sorted(source_dir.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name.startswith("."):
            continue
        if not (subdir / SKILL_MARKER).exists():
            continue

        name = subdir.name
        link_name = prefix + name
        validate_skill_name(link_name)
        dest = target_dir / link_name

        create_link(subdir, dest, force=True)
        click.echo(f"Linked {link_name}")
        linked += 1

    click.echo(f"Linked {linked} skill(s) from {source_dir}")
