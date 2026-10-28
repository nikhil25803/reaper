"""Command-line interface for Reaper."""

from typing import Annotated

import typer

from reaper import __version__

DESCRIPTION = "Reaper is a language-agnostic tool for dead code detection and analysis."

app = typer.Typer(
    add_completion=False,
    help=DESCRIPTION,
    invoke_without_command=True,
    name="reaper",
    no_args_is_help=False,
)


def version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(__version__)
        raise typer.Exit


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Detect potentially unused code in software projects."""
    if ctx.invoked_subcommand is None and not version:
        typer.echo(ctx.get_help())
