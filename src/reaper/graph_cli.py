"""Commands for exploring a generated code graph."""

import json
import math
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from reaper.utils.graph import (
    analyzed_projects,
    candidate_nodes,
    graph_path,
    load_graph,
    matching_nodes,
)

graph_app = typer.Typer(help="Explore a generated Graphify graph.")


def project_graph(project: Path) -> tuple[list[dict], list[dict]]:
    """Load a project graph or exit with an actionable error."""
    path = graph_path(project)
    try:
        return load_graph(path)
    except FileNotFoundError as error:
        typer.echo(f"Graph not found at {path}. Run reaper --scan first.", err=True)
        raise typer.Exit(1) from error
    except (OSError, json.JSONDecodeError, ValueError) as error:
        typer.echo(f"Unable to read graph: {error}", err=True)
        raise typer.Exit(1) from error


@graph_app.command()
def projects(
    root: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
            metavar="ROOT",
            help="Directory to search for analyzed projects.",
        ),
    ] = Path("."),
) -> None:
    """List project paths containing generated Reaper graphs."""
    found = analyzed_projects(root)
    if not found:
        typer.echo(f"No analyzed projects found under {root}.")
        return

    table = Table(title="Analyzed Projects")
    table.add_column("Project")
    table.add_column("Project path", overflow="fold")
    displayed_paths: list[str] = []
    for project in found:
        displayed_path = os.path.relpath(project, Path.cwd())
        displayed_paths.append(displayed_path)
        table.add_row(project.name, displayed_path)
    Console().print(table)
    typer.echo(f"Found {len(found)} analyzed project(s).")
    typer.echo(
        f'Next: reaper graph candidates "{displayed_paths[0]}" '
        "--list --limit 10 --page 1"
    )


@graph_app.command()
def candidates(
    project: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
            metavar="PROJECT_PATH",
            help="Project directory containing reaper-analysis.",
        ),
    ] = Path("."),
    list_: Annotated[
        bool, typer.Option("--list", help="Display a page of candidate details.")
    ] = False,
    limit: Annotated[
        int, typer.Option(min=1, max=100, help="Candidates per page.")
    ] = 10,
    page: Annotated[int, typer.Option(min=1, help="One-based page number.")] = 1,
) -> None:
    """List callable nodes with no incoming usage connections."""
    nodes, edges = project_graph(project)
    found = candidate_nodes(nodes, edges)
    console = Console()
    console.print(
        "[yellow]Review candidates only: entry points, public APIs, decorators, "
        "reflection, and framework hooks can appear unused.[/yellow]"
    )
    if not found:
        typer.echo("No zero-inbound callable candidates found.")
        return
    if not list_:
        if page != 1:
            raise typer.BadParameter("--page requires --list", param_hint="--page")
        typer.echo(f"Found {len(found)} possible dead-code candidates.")
        typer.echo(
            f'Next: reaper graph candidates "{project}" --list --limit {limit} --page 1'
        )
        return

    total = len(found)
    total_pages = math.ceil(total / limit)
    if page > total_pages:
        raise typer.BadParameter(
            f"page {page} is out of range; valid pages are 1-{total_pages}",
            param_hint="--page",
        )
    start = (page - 1) * limit
    displayed = found[start : start + limit]

    console.print()
    table = Table(title="Possible Dead-Code Candidates")
    table.add_column("Node ID", overflow="fold")
    table.add_column("Symbol")
    table.add_column("Source", overflow="fold")
    table.add_column("Line")
    table.add_column("Outgoing", justify="right")
    for node, outgoing in displayed:
        table.add_row(
            str(node["id"]),
            str(node.get("label") or node.get("id")),
            str(node["source_file"]),
            str(node.get("source_location") or "-"),
            str(outgoing),
        )
    console.print(table)
    typer.echo()
    end = start + len(displayed)
    typer.echo(
        f"Page {page}/{total_pages} · Showing {start + 1}-{end} of {total} candidates"
    )
    typer.echo()
    typer.echo(f'Inspect: reaper graph inspect "{project}" "{displayed[0][0]["id"]}"')
    if page < total_pages:
        typer.echo(
            f'Next: reaper graph candidates "{project}" --list '
            f"--limit {limit} --page {page + 1}"
        )


@graph_app.command()
def inspect(
    project: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
            help="Project directory containing reaper-analysis.",
        ),
    ],
    node: Annotated[str, typer.Argument(help="Exact node ID or label.")],
    limit: Annotated[
        int, typer.Option(min=1, help="Maximum connections to display.")
    ] = 50,
) -> None:
    """Show one node and its incoming and outgoing relationships."""
    nodes, edges = project_graph(project)
    matches = matching_nodes(nodes, node)
    if not matches:
        typer.echo(f"Node not found: {node}", err=True)
        raise typer.Exit(1)
    if len(matches) > 1:
        typer.echo("Ambiguous node label. Use an exact node ID:", err=True)
        for match in matches:
            typer.echo(f"  {match.get('id')}", err=True)
        raise typer.Exit(2)

    selected = matches[0]
    selected_id = selected.get("id")
    console = Console()
    details = Table(title="Graph Node", show_header=False)
    details.add_column("Field")
    details.add_column("Value")
    for field, value in (
        ("ID", selected_id),
        ("Label", selected.get("label")),
        ("Source", selected.get("source_file")),
        ("Location", selected.get("source_location")),
        ("Community", selected.get("community")),
        ("Origin", selected.get("_origin")),
    ):
        details.add_row(field, str(value) if value is not None else "-")
    console.print(details)

    labels = {item.get("id"): item.get("label") for item in nodes}
    connections: list[tuple[str, str, str]] = []
    for edge in edges:
        if edge.get("source") == selected_id:
            neighbor = edge.get("target")
            connections.append(
                (
                    "out",
                    str(edge.get("relation") or "-"),
                    str(labels.get(neighbor) or neighbor),
                )
            )
        if edge.get("target") == selected_id:
            neighbor = edge.get("source")
            connections.append(
                (
                    "in",
                    str(edge.get("relation") or "-"),
                    str(labels.get(neighbor) or neighbor),
                )
            )

    if not connections:
        typer.echo("No connections found.")
        return

    connections.sort()
    table = Table(title=f"Connections ({len(connections)} total)")
    table.add_column("Direction")
    table.add_column("Relation")
    table.add_column("Node")
    for direction, relation, neighbor in connections[:limit]:
        table.add_row(direction, relation, neighbor)
    console.print(table)
