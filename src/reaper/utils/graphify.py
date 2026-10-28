"""Graphify executable integration."""

import shutil
import subprocess
from pathlib import Path

import typer


def graphify_executable() -> str:
    """Return the Graphify executable or exit with installation guidance."""
    executable = shutil.which("graphify")
    if executable is None:
        typer.echo(
            "Graphify is not installed. Install it with: uv tool install graphifyy",
            err=True,
        )
        raise typer.Exit(1)
    return executable


def run_graphify_check(tool: str) -> None:
    """Report the installed Graphify version."""
    if tool.casefold() != "graphify":
        raise typer.BadParameter("only graphify is supported", param_hint="--check")

    try:
        result = subprocess.run(
            [graphify_executable(), "--version"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as error:
        typer.echo(f"Unable to run Graphify: {error}", err=True)
        raise typer.Exit(1) from error

    if result.returncode != 0:
        if result.stderr:
            typer.echo(result.stderr.rstrip(), err=True)
        raise typer.Exit(result.returncode if result.returncode > 0 else 1)

    typer.echo(result.stdout.strip() or "Graphify is installed.")


def run_graphify_scan(scan_path: Path) -> None:
    """Generate a local, code-only graph for a project."""
    output_root = scan_path / "reaper-analysis"
    command = [
        graphify_executable(),
        "extract",
        str(scan_path),
        "--out",
        str(output_root),
        "--code-only",
    ]

    try:
        result = subprocess.run(command, check=False)
    except OSError as error:
        typer.echo(f"Unable to run Graphify: {error}", err=True)
        raise typer.Exit(1) from error

    if result.returncode != 0:
        raise typer.Exit(result.returncode if result.returncode > 0 else 1)

    typer.echo(f"Analysis written to {output_root / 'graphify-out'}")
