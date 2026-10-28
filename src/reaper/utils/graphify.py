"""Graphify executable integration."""

import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table


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
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as error:
        typer.echo(f"Unable to run Graphify: {error}", err=True)
        raise typer.Exit(1) from error

    if result.returncode != 0:
        for output in (result.stdout, result.stderr):
            if output:
                typer.echo(output.rstrip(), err=True)
        raise typer.Exit(result.returncode if result.returncode > 0 else 1)

    graph_path = output_root / "graphify-out" / "graph.json"
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        typer.echo("Graphify completed but graph.json was not created.", err=True)
        raise typer.Exit(1) from error
    except (OSError, json.JSONDecodeError) as error:
        typer.echo(f"Unable to read Graphify output: {error}", err=True)
        raise typer.Exit(1) from error

    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        typer.echo("Graphify produced an invalid graph.json.", err=True)
        raise typer.Exit(1)

    nodes = graph["nodes"]
    edges = graph.get("links", graph.get("edges"))
    if not isinstance(edges, list) or not all(isinstance(node, dict) for node in nodes):
        typer.echo("Graphify produced an invalid graph.json.", err=True)
        raise typer.Exit(1)

    communities = {
        node["community"] for node in nodes if node.get("community") is not None
    }
    table = Table(title="Reaper <> Graphify Scan Complete")
    table.add_column("Metric")
    table.add_column("Count", justify="right")
    table.add_row("Nodes", str(len(nodes)))
    table.add_row("Edges", str(len(edges)))
    table.add_row("Communities", str(len(communities)))
    Console().print(table)
