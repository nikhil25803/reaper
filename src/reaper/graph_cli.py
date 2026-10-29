"""Commands for exploring a generated code graph."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from reaper.utils.graph import candidate_nodes, graph_path, load_graph, matching_nodes

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
def candidates(
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
    limit: Annotated[
        int, typer.Option(min=1, help="Maximum candidates to display.")
    ] = 20,
) -> None:
    """List callable nodes with no incoming usage connections."""
    nodes, edges = project_graph(project)
    found = candidate_nodes(nodes, edges, limit)
    console = Console()
    console.print(
        "[yellow]Review candidates only: entry points, public APIs, decorators, "
        "reflection, and framework hooks can appear unused.[/yellow]"
    )
    if not found:
        typer.echo("No zero-inbound callable candidates found.")
        return

    table = Table(title="Possible Dead-Code Candidates")
    table.add_column("Symbol")
    table.add_column("Source")
    table.add_column("Line")
    table.add_column("Outgoing", justify="right")
    for node, outgoing in found:
        table.add_row(
            str(node.get("label") or node.get("id")),
            str(node["source_file"]),
            str(node.get("source_location") or "-"),
            str(outgoing),
        )
    console.print(table)


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
