"""Graph loading and analysis helpers."""

import json
import os
from pathlib import Path, PurePosixPath

IGNORED_USAGE_RELATIONS = {"contains", "rationale_for"}
TEST_DIRECTORIES = {"test", "tests", "__tests__"}
DISCOVERY_EXCLUDES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "reaper-analysis",
}


def graph_path(project: Path) -> Path:
    """Return the generated graph path for a project."""
    return project / "reaper-analysis" / "graphify-out" / "graph.json"


def analyzed_projects(root: Path) -> list[Path]:
    """Find scan paths containing a generated Reaper graph."""
    projects: list[Path] = []
    for current, directories, _ in os.walk(root):
        project = Path(current)
        if graph_path(project).is_file():
            projects.append(project.resolve())
        directories[:] = [
            directory
            for directory in directories
            if directory not in DISCOVERY_EXCLUDES
        ]
    return sorted(projects, key=lambda project: project.as_posix())


def load_graph(path: Path) -> tuple[list[dict], list[dict]]:
    """Load and validate the node and edge collections in a graph."""
    graph = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list):
        raise ValueError("invalid graph.json")

    nodes = graph["nodes"]
    edges = graph.get("links", graph.get("edges"))
    if (
        not isinstance(edges, list)
        or not all(isinstance(node, dict) for node in nodes)
        or not all(isinstance(edge, dict) for edge in edges)
    ):
        raise ValueError("invalid graph.json")
    return nodes, edges


def is_test_source(source: str) -> bool:
    """Return whether a source path follows a common test convention."""
    path = PurePosixPath(source.replace("\\", "/"))
    name = path.name.casefold()
    stem = path.stem.casefold()
    return (
        any(part.casefold() in TEST_DIRECTORIES for part in path.parts)
        or name.startswith("test_")
        or stem.endswith("_test")
        or ".test." in name
        or ".spec." in name
    )


def usage_edges(edges: list[dict]) -> list[dict]:
    """Return non-structural, non-self graph edges."""
    return [
        edge
        for edge in edges
        if edge.get("relation") not in IGNORED_USAGE_RELATIONS
        and edge.get("source") != edge.get("target")
    ]


def candidate_nodes(nodes: list[dict], edges: list[dict]) -> list[tuple[dict, int]]:
    """Return local callable nodes with no incoming usage edges."""
    relevant_edges = usage_edges(edges)
    incoming = {edge.get("target") for edge in relevant_edges}
    outgoing: dict[object, int] = {}
    for edge in relevant_edges:
        source = edge.get("source")
        outgoing[source] = outgoing.get(source, 0) + 1

    candidates = [
        (node, outgoing.get(node.get("id"), 0))
        for node in nodes
        if node.get("_origin") == "ast"
        and node.get("_callable") is True
        and node.get("file_type") == "code"
        and node.get("external") is not True
        and isinstance(node.get("id"), str)
        and isinstance(node.get("source_file"), str)
        and not is_test_source(node["source_file"])
        and node.get("id") not in incoming
    ]
    candidates.sort(
        key=lambda item: (
            item[1],
            item[0]["source_file"],
            _line_number(item[0].get("source_location")),
        )
    )
    return candidates


def matching_nodes(nodes: list[dict], query: str) -> list[dict]:
    """Find a node by exact ID or normalized label."""
    exact = [node for node in nodes if node.get("id") == query]
    if exact:
        return exact

    normalized_query = query.casefold().removesuffix("()")
    return [
        node
        for node in nodes
        if any(
            isinstance(value, str)
            and value.casefold().removesuffix("()") == normalized_query
            for value in (node.get("label"), node.get("norm_label"))
        )
    ]


def _line_number(location: object) -> int:
    """Return a sortable line number from Graphify's location value."""
    try:
        return int(str(location).removeprefix("L").split("-", 1)[0])
    except ValueError:
        return 0
